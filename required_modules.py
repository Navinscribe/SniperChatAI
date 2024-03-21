#!/usr/bin/env python3

try:
    # Import the standard modules
    import argparse
    import asyncio
    import json
    import logging
    import os
    import sys
    import time

    # Import the third-party modules
    import aiofiles
    import aiohttp
    import argcomplete
    import yaml
    from alive_progress import alive_bar
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()  # Load the .env file

# Handle the missing modules
except ModuleNotFoundError as e:
    missing_module = e.name

    if missing_module == 'argcomplete':
        action = "Install it using 'pip install argcomplete && activate-global-python-argcomplete'."
    elif missing_module == 'dotenv':
        action = "Install it using 'pip install python-dotenv'."
    elif missing_module == 'yaml':
        action = "Install it using 'pip install PyYAML'."
    elif missing_module in ['aiofiles', 'aiohttp', 'alive_progress', 'openai', 'portalocker']:
        action = f"Install it using 'pip install {missing_module}'."
    else:
        action = "Consider upgrading Python."

    print(f"\033[91m\n[⛔] Error: Required Python module '{missing_module}' is missing. {action} "
          f"Exiting program.\n\033[00m")
    exit(1)
