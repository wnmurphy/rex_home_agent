# Rex Home Agent

Rex Home Agent is a personal AI assistant.

Now that consumer hardware can run local LLMs fairly easily, I wanted to see if I could build a private voice assistant.

Should:
* work out-of-the-box on any M4 Mac
* have persistent memory
* have tool usage (i.e. do a web search for information past the model's cutoff date)
* support barge-in (user can interrupt voice output)


This project was developed with PyCharm integrated with local models via the Continue plugin and ollama. 
I used `qwen3-coder:30b` for the IDE agent, and `qwen2.5-coder:7b` for in-editor autocomplete.

## Requirements

This should run comfortably on a MacBook Pro, Mac Mini, Mac Studio, etc. with:
* an M4 chip
* 48GB RAM
* 14 CPU cores
* 20 GPU cores

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
9. Start the agent with `python main.py`


## Customize your wake word

In your [Picovoice console](https://console.picovoice.ai/ppn), create a new Porcupine wake word model and download it. 

Add the file to `/models` and update the path to this model as `PORCUPINE_WAKE_WORD_PATH` in `config.py`.

## Architecture

The agent is structured as a series of independent workers. 

Each worker handles a separate function, and runs in its own thread.

Data is streamed between workers via queues.

```
User voice input
↓
Microphone
↓
Audio Capture Worker
↓
[captured audio queue]
↓
Wake Word Detection Worker
↓ 
[speech audio queue]
↓
Speech-To-Text Worker
↓
[STT text queue]
↓
LLM Worker ←→ Agent (intent extraction, chat memory, tool selection)
↓
[LLM response queue]
↓
Text-To-Speech Worker
↓
[TTS audio queue]
↓
Speaker → Agent voice output
```

## TODO Items

- [ ] Implement barge-in
- [ ] Sustain conversation. Don't require wake word unless no user voice input for ~5 minutes, etc.
- [ ] Add Agent class from LangChain.
- [ ] Add model memory like MemoryBuffer from LangChain.
- [ ] Add a model call for intent extraction.
- [ ] Add tool to perform a web search.
- [ ] Add a sleep sound effect when the agent goes back to sleep.

## Miscellaneous


Sound credits:
* Wake sound: kickhat on [Freesound.org](https://freesound.org/people/kickhat/sounds/264447/)
* Thinking sound 1: Tissman on [Freesound.org](https://freesound.org/people/Tissman/sounds/521848)
* Thinking sound 2: DanJFilms on [Freesound.org](https://freesound.org/people/DanJFilms/sounds/845167/)