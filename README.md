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

- [ ] Implement barge-in
- [ ] Sustain conversation. Don't require wake word unless no user voice input for ~5 minutes, etc.
- [ ] Add Agent class from LangChain.
- [ ] Set a system prompt for agent, specific to voice mode (keep responses short, etc.)
- [ ] Add model memory like MemoryBuffer from LangChain.
- [ ] Add tool to perform a web search.
- [ ] Add a wake sound effect when the wake word is detected.
- [ ] Add a thinking sound effect when the agent is processing a response.
- [ ] Add a sleep sound effect when the agent goes back to sleep.