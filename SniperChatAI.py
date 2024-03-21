#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

# Import the required modules and the helper functions
from required_modules import aiofiles, aiohttp, alive_bar, asyncio, OpenAI, os
from helper import handle_error, FileParser, ArgumentParser, print_status_messages
from openai_api_request_wrapper import openai_api_request_wrapper


# Function to set up the OpenAI API client
def setup_openai_api_client():
    # Read the OpenAI API key from the .env file
    openai_api_key = os.getenv('OPENAI_API_KEY')

    # Exit if the API key is missing
    if not openai_api_key:
        handle_error("OPENAI_API_KEY environment variable not set. Aborting - no key, no ignition!",
                     "OPENAI_API_KEY environment variable was not set.")

    # Initialize the OpenAI API client with the provided API key
    client = OpenAI(api_key=openai_api_key)
    return client


# Function to verify the connection with the OpenAI API
async def verify_openai_api_connection(session, local_args, guidelines, client):
    # Dummy prompt for the connection verification request
    dummy_prompt = "Hello!"
    messages = [{"role": "system", "content": guidelines}, {"role": "user", "content": dummy_prompt}]

    # Query the OpenAI API with the prepared dummy message
    response = await openai_api_request_wrapper(session, client, local_args, messages)

    # If the connection is successful, print a success message on the terminal
    if response:
        print_status_messages("successful_connection_with_openai_api")


# Class to manage the conversation history
class ConversationHistoryManager:
    def __init__(self, conversation_mode):
        self.conversation_mode = conversation_mode  # Conversation mode (on/off)
        self.conversation_history = []

    # Method to add the current prompt to the conversation history
    def add_prompt_to_history(self, prompt):
        # If the conversation mode is on, append the current prompt to the existing conversation history
        if self.conversation_mode == 'on':
            self.conversation_history.append((prompt, ""))

        # If the conversation mode is off, replace the conversation history with only the current prompt
        elif self.conversation_mode == 'off':
            self.conversation_history = [(prompt, "")]

    # Method to update the latest response in the conversation history
    def update_latest_response(self, response):
        self.conversation_history[-1] = (self.conversation_history[-1][0], response)

    # Method to retrieve the complete conversation history
    def get_conversation_history(self):
        return self.conversation_history.copy()


# Class to manage the interactions with the OpenAI API
class OpenAIConversationManager:
    def __init__(self, local_args, client, guidelines):
        self.args = local_args
        self.client = client
        self.guidelines = guidelines
        self.conversation_context = ConversationHistoryManager(local_args.conversation_mode)
        self.results = []

    # Method to process the prompts and update the conversation history
    async def __call__(self, session, index_prompt_tuple, queue, bar=None):
        index, prompt = index_prompt_tuple  # Index and prompt for current conversation
        prompt = prompt.rstrip('\n')  # Remove trailing newlines from each prompt

        # Add the current prompt to the conversation history
        self.conversation_context.add_prompt_to_history(prompt)

        # Get the local conversation history after adding the prompt
        local_conversation_history = self.conversation_context.get_conversation_history()

        # Query the OpenAI API to generate responses based on the current conversation history
        responses = await self.query_openai_and_get_responses(session, local_conversation_history)

        # Update the conversation history with the responses
        if self.args.conversation_mode == 'on':
            for response in responses:
                # Reset the conversation history to its state before the responses were generated
                self.conversation_context.conversation_history = local_conversation_history.copy()
                self.conversation_context.update_latest_response(response)

        elif self.args.conversation_mode == 'off':
            for response in responses:
                self.conversation_context.update_latest_response(response)

        # Append the results and put them in the queue
        self.results.append((index, prompt, responses))
        await queue.put((index, prompt, responses))

        return index, prompt, responses

    # Method to query the OpenAI API with the prepared messages and get responses
    async def query_openai_and_get_responses(self, session, local_conversation_history):
        messages = [{"role": "system", "content": self.guidelines}]

        # Append the previous conversation history to the message
        for message in local_conversation_history:
            messages.append({"role": "user", "content": message[0]})
            messages.append({"role": "assistant", "content": message[1]})

        response = await openai_api_request_wrapper(session, self.client, self.args, messages)

        # Update the conversation history with the last appended prompt's response
        if response:
            # Treat each response from the OpenAI API as a separate response
            for choice in response:
                local_conversation_history[-1] = (local_conversation_history[-1][0], choice)

        return response


# Class to orchestrate the processing of prompts
class PromptOrchestrator:
    def __init__(self, conversation_manager):
        self.conversation_manager = conversation_manager
        self.file_lock = asyncio.Lock()  # Add a lock

    # Method to process prompts sequentially when the conversation mode is on
    async def process_prompts_sequentially(self, session, prompts):
        queue = asyncio.PriorityQueue()  # Queue to store results

        with alive_bar(len(prompts)) as bar:  # Display the progress bar
            for index, prompt in enumerate(prompts, start=1):
                index, prompt, responses = await self.conversation_manager(session, (index, prompt), queue, bar)
                # Write the output to the specified file immediately after processing each prompt
                await self.write_output_to_file(self.conversation_manager.args, (index, prompt, responses))
                bar()

    # Method to process prompts concurrently when the conversation mode is off
    async def process_prompts_concurrently(self, session, prompts):
        queue = asyncio.PriorityQueue()  # Queue to store results

        with alive_bar(len(prompts)) as bar:  # Display the progress bar
            writer_task = asyncio.create_task(self.cache_output(queue, bar))

            # Create a semaphore to limit the number of concurrent tasks
            semaphore = asyncio.Semaphore(self.conversation_manager.args.max_threads)

            # Create a task for each prompt, but limit the concurrency with the semaphore
            processor_tasks = [
                self.process_prompts_concurrently_with_delay(semaphore, session, (index, prompt), queue, bar)
                for index, prompt in enumerate(prompts, start=1)]

            await asyncio.gather(*processor_tasks)
            await queue.put((None, None, None))  # Signal the writer task to exit
            await writer_task

    # Method to process prompts concurrently with delay
    async def process_prompts_concurrently_with_delay(self, semaphore, session, index_prompt_tuple, queue, bar):
        async with semaphore:
            await asyncio.sleep(self.conversation_manager.args.delay)
            await self.conversation_manager(session, index_prompt_tuple, queue, bar)

    # Method to temporarily store the generated output
    async def cache_output(self, queue, bar):
        buffer = {}  # Buffer to store results
        next_index = 1  # Index for the next result
        while True:
            result = await queue.get()
            if result[0] is None:
                break
            index, prompt, responses = result  # Unpack the result
            buffer[index] = (prompt, responses)  # Store the result in the buffer

            # Write results to the specified file and update the progress bar
            while next_index in buffer:
                prompt, responses = buffer.pop(next_index)
                await self.write_output_to_file(self.conversation_manager.args, (next_index, prompt, responses))
                bar()
                next_index += 1

    # Method to write the generated output to the specified file
    async def write_output_to_file(self, local_args, result=None):

        # Use file_lock to ensure a thread-safe file access
        async with self.file_lock:

            # Open the output file in append mode
            async with aiofiles.open(local_args.output_file, mode='a', newline='') as f:

                # Write the header row if the file is empty
                if (await f.tell()) == 0:  # Check if the file pointer is at the beginning
                    await f.write("#,Prompt,Response\n")

                if result:
                    for response in result[2]:
                        # Encapsulate the prompt and response in quotes to preserve commas and newlines
                        quoted_prompt = '"' + result[1].replace('"', '""') + '"'
                        quoted_response = '"' + response.replace('"', '""') + '"'
                        await f.write(','.join([str(result[0]), quoted_prompt, quoted_response]) + '\n')


# Main function to orchestrate program execution
async def main():
    # Parse the command-line arguments
    args = ArgumentParser().parse_arguments()

    # Initialize an OpenAI API client instance
    client = setup_openai_api_client()

    # Read prompts and guidelines from the provided input files
    file_parser = FileParser(prompts_file=args.prompts_file, guidelines_file=args.guidelines_file)
    prompts, guidelines = await file_parser.parse_input_files()

    # Initialize an OpenAIConversationManager instance
    conversation_manager = OpenAIConversationManager(args, client, guidelines)

    # Initialize a PromptOrchestrator instance
    prompt_orchestrator = PromptOrchestrator(conversation_manager)

    # Set up the output file
    await prompt_orchestrator.write_output_to_file(args)

    # Query the OpenAI API using the prompts and write the generated output to the specified file
    async with aiohttp.ClientSession() as session:
        await verify_openai_api_connection(session, args, guidelines, client)  # Verify connection with the OpenAI API
        if args.conversation_mode == 'on':
            await prompt_orchestrator.process_prompts_sequentially(session, prompts)
        elif args.conversation_mode == 'off':
            await prompt_orchestrator.process_prompts_concurrently(session, prompts)

    # Print a success message on the terminal
    print_status_messages("successful_program_execution", args)


# Starting point for the program
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n")
        handle_error(
            "Launch sequence interrupted! Fear not, this program saves partial output. Retrieve it when ready.",
            "Program interrupted. Partial output may have been generated.")
