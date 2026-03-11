# Rex Home Agent

Rex Home Agent is a personal AI assistant.

## Setup

1. Install Homebrew if you don't already have it installed:
    ```
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
    ```
2. Install Ollama with `brew install ollama`.
3. Start Ollama with `brew services start ollama`.
4. Download a model like Mistral Small with `ollama pull huihui_ai/mistral-small-abliterated:latest`.
5. Set this model name as `OLLAMA_MODEL` in config.py
6. Activate the virtual environment with `source .venv/bin/activate`.
7. Install Python dependencies with `pip3 install -r requirements.txt`. 
8. Get a [Picovoice license key](https://console.picovoice.ai/signup) and set it as `PICOVOICE_LICENSE_KEY` in your environment variables.


## TODO Items

- [ ] Modify worker class to accept an instance of library (recorder or speaker) instead of only Queue
- [ ] Implement individual worker logic.
- [ ] Sustain conversation. Only require wake word after ~5 minutes of no user input or model response.
- [ ] Add Agent class from LangChain.
- [ ] Set a system prompt for agent, specific to voice mode (keep responses short, etc.)
- [ ] Add model memory like MemoryBuffer from LangChain.
- [ ] Add tool to perform a web search.
- [ ] Add a thinking sound effect when the agent is processing a response.