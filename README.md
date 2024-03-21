<p align="center">
<img src = "https://raw.githubusercontent.com/Navinscribed/media-repo/master/SniperChatAI/SniperChatAI.gif">
</p>

<p align="center">
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/language-python%203.x-blue">
  </a>
  <a href="https://openai.com/">
    <img src="https://img.shields.io/badge/ai_platform-OpenAI-orange">
 </a>
  <a href="https://github.com/Navinscribed">
    <img src="https://img.shields.io/badge/author-Navinscribed-brightgreen">
 </a>
</p>

## SniperChatAI
**SniperChatAI** is a Python-based chatbot simulator powered using OpenAI that allows rapid evaluation of prompts in a controlled space.
<br><br>
## Features
- **Chatbot Behaviour Customization:** Lets you customize the behaviour of the chatbot using a predefined set of guidelines. These guidelines help in shaping the responses of the chatbot.

- **Automated Querying & Documentation:** Queries OpenAI with the supplied prompts, retrieves the response(s) for each prompt, and records the generated output in a CSV file.

- **Prompt Processing Flexibility:** Supports sequential as well as concurrent processing of prompts.

- **Conversation Simulation:** Keeps track of conversation history, effectively simulating a chatbot that remembers past interactions. Prompts are processed sequentially in this scenario.

- **Control Over Context:** Alternatively, you can disable the conversation history when a context isn't necessary, allowing you to focus solely on how the chatbot responds to your prompts. Prompts are processed concurrently in this scenario. Rest assured, the results shall be printed sequentially in the output file.

- **Resilient Output Generation:** Capable of saving partially generated results. Useful during abrupt program termination scenarios.
<br>

> **Note**
>
> While SniperChatAI currently only supports OpenAI, the underlying code could be adapted to work with other AI vendors and models. The modular design of the program makes it relatively straightforward to replace the OpenAI-specific parts with equivalent components for another AI vendor.

<br>

## Why Use SniperChatAI?
- SniperChatAI can be an invaluable tool for developers and application teams who are in the process of developing a chatbot. You can evaluate how well the chatbot adheres to its operating guidelines and how effective its guidelines really are, by examining the responses it generates for various prompts.

- In situations where the chatbot deviates from the anticipated behaviour, developers can leverage these insights to refine the guidelines, thereby improving the chatbot’s alignment with its intended functionality.

- It efficiently handles a substantial volume of prompts, which can save significant time and effort.

- Security teams can use SniperChatAI to simulate various threat scenarios. By crafting specific prompts, you can gauge how a malicious actor might use your chatbot for nefarious purposes. You can also check the data privacy aspect by supplying prompts that are not expected to yield certain types of information (such as PII or PCI), and verify whether the chatbot respects these boundaries.

- In a nutshell, SniperChatAI is more than just a chatbot simulator. It’s a robust tool for testing and refining, designed to be a sturdy companion throughout the extensive and iterative process of chatbot development.
<br><br>
## Requirements
1. **Python 3.7+**

2. **An active OpenAI API key** with permission to access the endpoint `/v1/chat/completions`. Get yours [here](https://platform.openai.com/account/api-keys).

3. The program expects two input files:
   1. **Guidelines file**: A file containing guidelines that define the chatbot's behaviour. In technical terms, these are referred to as the `System Prompts`.
   2. **Prompts file**: A file containing prompts to query the chatbot, with each prompt written on a separate line. These are referred to as the `User Prompts`.

      **Note:** The repo includes sample input files to give you an idea of what the file contents might look like.
<br><br>
## Installation Steps
1. Download or clone the repository.

2. Install the dependencies using the command:
```
pip install -r requirements.txt
```
3. Prepare and place the two required input files (a guidelines file and a prompts file) inside the cloned repository.

4. Place your OpenAI API key in a file named `.env` inside the same folder.
<br><br>
## Usage

### Command
```
python SniperChatAI.py --ai_model gpt-4 --guidelines_file guidelines.txt --prompts_file prompts.txt
```

### Program Arguments
#### Required Arguments
- `--ai_model` : Name of the chat-based AI model, such as gpt-4

- `--guidelines_file` : File containing guidelines that define the chatbot’s behaviour

- `--prompts_file` : File containing prompts to query the chatbot
<br><br>
#### Optional Arguments
- `--max_tokens` : Maximum words in each response per prompt (Default: `100`)

- `-n` : Number of responses to be generated per prompt (Default: `1`)

- `--stop` : Word or phrase after which the response generation stops (Default: `None`)

- `--temperature` : Controls the response randomness. Allowed range: [0.0,1.0]. (Default: `0.5`)

- `--conversation_mode` :

  - `on` : Persists conversation history across prompts (Default: `on`)

  - `off` : Does not persist conversation history between prompts

- `--max_threads` : Maximum concurrent threads to process the prompts (Default: `10`)

- `--delay` : Delay in seconds between each thread. (Default: `0`)

- `--output_file` : Output CSV file name (Default: `output.csv`)

- `-h` / `--help` : Shows the help message and exits

<br>

> **Note**
> 
> The arguments `--max_threads` and `--delay` are only applied when `--conversation_mode` is off.
> 
> The repo also includes a handy `config.yaml` file that lets you adjust the default values of the above arguments and a few other program parameters.


<br>

## License & Contributions
- This project is licensed under the terms of the MIT license. Feel free to contribute, go ahead and submit a [Pull Request](https://github.com/Navinscribed/SniperChatAI/pulls).

- However, if you are considering making significant modifications, I would insist that you discuss with me first by opening an [Issue](https://github.com/Navinscribed/SniperChatAI/issues/new).
<br><br>
---
<span style="vertical-align: middle;">Like my work?</span>
<a href="https://www.buymeacoffee.com/navin.m" style="vertical-align: middle;">
  Buy me a coffee maybe?
  <img src="https://cdn.buymeacoffee.com/buttons/bmc-new-btn-logo.svg" style="width: 30px; height: 30px; vertical-align: middle;">
</a>
