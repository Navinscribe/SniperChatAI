#!/usr/bin/env python3

# Import the required modules and the helper functions
from helper import config, handle_error
from required_modules import json


# Wrapper for making HTTP POST requests to the OpenAI API
async def openai_api_request_wrapper(session, client, args, messages):
    url = config.get('openai_api_url')
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {client.api_key}"
    }
    payload = {
        "model": args.ai_model,
        "messages": messages,
        "max_tokens": args.max_tokens,
        "n": args.n,
        "stop": args.stop,
        "temperature": args.temperature
    }
    try:
        async with session.post(url, headers=headers, data=json.dumps(payload)) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise Exception(data["error"]["message"])  # Extract the relevant portion from the error message
            return [choice["message"]["content"] for choice in data["choices"]]

    # Handle potential errors
    except Exception as OpenAIError:
        handle_error(f"Connection issue with the OpenAI API. Received the following response ➔ {OpenAIError}",
                     f"Connection issue with the OpenAI API. Received the following response ➔ {OpenAIError}.")
