#!/usr/bin/env python3

# Import the required modules
from required_modules import aiofiles, argcomplete, argparse, logging, os, sys, time, yaml

# Define the colour codes
RED = 91
GREEN = 92
BLUE = 94
YELLOW = 33


# Function to print coloured texts
def print_coloured(colour_code, coloured_text):
    print("\033[{}m{}\033[00m".format(colour_code, coloured_text))


# Get the program name
program_name = os.path.basename(sys.argv[0]).split('.')[0]

# Print the program summary
print_coloured(BLUE, f"\n"
                     f"[➤] Program Author: Navin M. (GitHub Handle: Navinscribed)\n\n"
                     f"[➤] {program_name} is a customizable chatbot powered using OpenAI\n    "
                     f"that allows rapid evaluation of prompts in a controlled space\n\n"
                     f"    --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ----\n"
                     f"    {program_name} | Automation? Check! Coherence? Check! Wit? Always!\n"
                     f"    --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ----\n")

# Set up logging
logging.basicConfig(filename=f"log_{program_name}.log", filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.WARNING)


# Function to handle errors
def handle_error(error_message, log_message, is_warning=False):
    prefix = "[🚧] Warning: " if is_warning else "[⛔] Error: "
    colour_code = YELLOW if is_warning else RED

    print_coloured(colour_code, f"{prefix}{error_message}\n")

    if is_warning:
        logging.warning(log_message)
    else:
        logging.error(f"{log_message} Exited program.")
        exit(1)


# Function to load the configuration from the config.yaml file
def load_config():
    try:
        with open('config.yaml') as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        handle_error("Mission-critical file 'config.yaml' missing! Aborting launch!",
                     "Config file 'config.yaml' could not be found.")
        exit(1)
    except yaml.YAMLError as e:
        handle_error(f"Error loading the configuration from 'config.yaml': {e}. Exiting program.",
                     "Error loading the configuration from 'config.yaml'.")
        exit(1)


# Load the configuration from the config.yaml
config = load_config()

# Override logging level if specified
logging_level = config.get('logging_level')  # Get default logging level from config.yaml
logging_level = getattr(logging, logging_level.upper())  # Convert the string to its matching logging level constant
logging.getLogger().setLevel(logging_level)


# Class to manage validation and parsing of command-line arguments
class ArgumentParser:
    # Retrieve the default values from config.yaml
    def __init__(self):
        self.default_max_tokens = config.get('max_tokens')
        self.default_n = config.get('n')
        self.default_stop = config.get('stop')
        self.min_temperature = config['temperature']['min']
        self.max_temperature = config['temperature']['max']
        self.default_temperature = config['temperature']['default']
        self.default_output_file = config.get('output_file')
        self.default_conversation_mode = config.get('conversation_mode').lower()
        self.default_max_threads = config.get('max_threads')
        self.default_delay = config.get('delay')

    # Method to validate the arguments
    @staticmethod
    def validate_arg(value, arg_name, expected_type):
        # Validate the argument type
        try:
            value = expected_type(value)
        except ValueError:
            logging.error(f"Invalid value '{value}' provided for the argument '{arg_name}'. Exited program.")
            raise argparse.ArgumentTypeError(f"\033[91mInvalid value '{value}' provided for the argument '{arg_name}'. "
                                             f"Has to be a number.\n\033[0m")

        # Validate that the argument is a positive integer
        if expected_type == int and value <= 0:
            logging.error(f"Invalid value '{value}' provided for the argument '{arg_name}'. Exited program.")
            raise argparse.ArgumentTypeError(f"\033[91mInvalid value '{value}' provided for the argument '{arg_name}'. "
                                             f"Has to be a positive non-zero integer.\n\033[0m")
        return value

    # Method to define the required arguments
    @staticmethod
    def define_required_args(parser):
        required_args = parser.add_argument_group('required arguments')
        required_args.add_argument('--ai_model', type=str, required=True,
                                   help='Name of the chat-based AI model (Example: gpt-4)')
        required_args.add_argument('--guidelines_file', type=str, required=True,
                                   help="File containing guidelines that define the chatbot's behaviour")
        required_args.add_argument('--prompts_file', type=str, required=True,
                                   help='File containing prompts to query the chatbot')
        return parser

    # Method to define the optional arguments
    def define_optional_args(self, parser):
        optional_args = parser.add_argument_group('optional arguments')
        optional_args.add_argument('--max_tokens',
                                   type=lambda value: self.validate_arg(value, '--max_tokens', int),
                                   default=self.default_max_tokens,
                                   help=f'Maximum words in each response per prompt '
                                        f'(Default: {self.default_max_tokens})')
        optional_args.add_argument('-n', type=lambda value: self.validate_arg(value, '-n', int),
                                   default=self.default_n,
                                   help=f'Number of responses to be generated per prompt (Default: {self.default_n})')
        optional_args.add_argument('--stop', type=str, default=self.default_stop,
                                   help=f'Word or phrase after which the response generation stops '
                                        f'(Default: {self.default_stop})')
        optional_args.add_argument('--temperature', default=self.default_temperature,
                                   type=lambda value: self.validate_arg(value, '--temperature', float),
                                   help=f'Controls the response randomness. '
                                        f'Allowed range: [{self.min_temperature},{self.max_temperature}] '
                                        f'(Default: {self.default_temperature})')
        optional_args.add_argument('--conversation_mode', type=str, default=self.default_conversation_mode,
                                   help=f'on: Persists conversation history across prompts '
                                        f'(Default: {self.default_conversation_mode})\n'
                                        'off: Does not persist conversation history between prompts')
        optional_args.add_argument('--max_threads',
                                   type=lambda value: self.validate_arg(value, '--max_threads', int),
                                   default=self.default_max_threads,
                                   help=f'Maximum concurrent threads to process the prompts '
                                        f'(Default: {self.default_max_threads})\n'
                                        '(Note: This setting is only applied when --conversation_mode is off)')
        optional_args.add_argument('--delay', type=lambda value: self.validate_arg(value, '--delay', int),
                                   default=self.default_delay,
                                   help=f'Delay in seconds between each thread (Default: {self.default_delay})\n'
                                        '(Note: This setting is only applied when --conversation_mode is off)')
        optional_args.add_argument('--output_file', type=str, default=self.default_output_file,
                                   help=f'Output CSV file name (Default: {self.default_output_file})')
        optional_args.add_argument('-h', '--help', action='help', help='Shows this help message and exits')

        return parser

    # Method to validate the '--conversation_mode' argument value
    @staticmethod
    def validate_conversation_mode(args):
        # Convert the provided value to lowercase
        args.conversation_mode = args.conversation_mode.lower()

        if args.conversation_mode not in ['on', 'off']:
            handle_error(f"Warp drive malfunction! Argument '--conversation_mode' expecting values 'on' or 'off'. "
                         f"Received '{args.conversation_mode}'. Launch sequence aborted!",
                         f"Invalid value '{args.conversation_mode}' provided for the argument '--conversation_mode'.")
            exit(1)

    # Method to clamp the '--temperature' argument value
    def clamp_temperature(self, args):
        if not (self.min_temperature <= args.temperature <= self.max_temperature):
            handle_error(
                f"Temperature anomaly detected. Allowed range [{self.min_temperature}, {self.max_temperature}]. "
                f"Received '{args.temperature}'. "
                f"Defaulting to '{self.default_temperature}' for a controlled propulsion.",
                f"Value '{args.temperature}' provided for the argument '--temperature' is outside allowed range "
                f"[{self.min_temperature}, {self.max_temperature}]. "
                f"Program proceeded to execute with default value '{self.default_temperature}'.",
                is_warning=True)
            args.temperature = self.default_temperature

    # Method to parse the arguments
    def parse_arguments(self):
        parser = argparse.ArgumentParser(
            description=f"example: python {program_name}.py --ai_model gpt-4 --guidelines_file guidelines.txt "
                        f"--prompts_file prompts.txt",
            add_help=False, formatter_class=argparse.RawTextHelpFormatter)

        parser = self.define_required_args(parser)  # Define the required arguments
        parser = self.define_optional_args(parser)  # Define the optional arguments

        argcomplete.autocomplete(parser)  # Enable autocomplete for the arguments
        args = parser.parse_args()

        self.validate_conversation_mode(args)  # Validate --conversation_mode
        self.clamp_temperature(args)  # Clamp --temperature

        args.output_file = get_unique_output_filename(args.output_file)  # Get a unique filename

        return args


# Class to parse the input files
class FileParser:
    def __init__(self, prompts_file, guidelines_file):
        self.prompts_file = prompts_file
        self.guidelines_file = guidelines_file

    # Method to open and read a file
    @staticmethod
    async def read_file_contents(filename):
        try:
            async with aiofiles.open(filename, 'r') as file:
                async for line in file:
                    yield str(line).strip()
        except FileNotFoundError:
            handle_error(f"Mission-critical file '{filename}' missing! Aborting launch!",
                         f"File '{filename}' could not be found.")
            exit(1)

    # Method to parse the prompts file and the guidelines file
    async def parse_input_files(self):
        prompts = [line async for line in self.read_file_contents(self.prompts_file) if line]
        guidelines = ' '.join([line async for line in self.read_file_contents(self.guidelines_file)])

        # Exit if the prompts file is empty
        if not prompts or not any(line.strip() for line in prompts):
            handle_error(f"Prompts file '{self.prompts_file}' is as empty as a vacuum in deep space. "
                         f"Program requires prompts for propulsion. Aborting launch!",
                         f"Prompts file '{self.prompts_file}' was empty.")

        # Warn and proceed if the guidelines file is empty
        if not guidelines.strip():
            handle_error(
                f"No guidelines in '{self.guidelines_file}' ➔ Expect unfiltered responses from the chatbot!",
                f"Guidelines file '{self.guidelines_file}' was empty. "
                f"Program proceeded to execute with limitations.", is_warning=True)

        return prompts, guidelines


# Function to ensure that the generated output file has a unique filename
def get_unique_output_filename(filename):
    base_filename = filename.split('.')[0]
    extension = '.csv'  # Default to .csv

    new_filename = f"{base_filename}{extension}"
    counter = 1

    while os.path.exists(new_filename):
        new_filename = f"{base_filename}_{counter}{extension}"
        counter += 1

    return new_filename


# Function to print status messages on the terminal during different stages of the program execution
def print_status_messages(event, args=None):
    messages = {
        "successful_connection_with_openai_api": [
            "[🌐] Connection with OpenAI API ✅                 (Possibilities upgraded to infinite!)\n",
            "[🔍] Program inputs verified ✅                    (Ready for launch. Clear skies ahead!)\n",
            "[🚀] Launching main program ✅                     (See you on the other side, slick!)\n"
        ],
        "successful_program_execution": [
            f"\n[🌟] Program aced its mission ✅                   (Excelsior!)\n",
            f"[📂] Output neatly cataloged in '{args.output_file}' ✅    (Peek if intrigued!)\n" if args else ""
        ]
    }

    for message in messages.get(event, []):
        print_coloured(GREEN, message)
        time.sleep(0.5)  # Introduce a small delay between each status message
