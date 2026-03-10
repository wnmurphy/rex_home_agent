# Rex Home Agent

Rex Home Agent is a personal AI assistant.

## Setup

1. Install Homebrew if you don't already have it installed:
    ```
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
    ```
1. Install Ollama with `brew install ollama`.
2. Start Ollama with `brew services start ollama`.
3. Download a model like Mistral Small with `ollama pull huihui_ai/mistral-small-abliterated:latest`.
4. Set this model name as `OLLAMA_MODEL` in config.py
5. Activate the virtual environment with `source .venv/bin/activate`.
6. Install Python dependencies with `pip3 install -r requirements.txt`. 
7. Get a [Picovoice license key](https://console.picovoice.ai/signup) and set it as `PICOVOICE_LICENSE_KEY` in your environment variables.