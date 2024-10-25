# Ollama Streamlit App

Streamlit app that allows you to chat with local Ollama models and save the chat history automatically to a json file `chats.json`.

![stapp](https://github.com/user-attachments/assets/5bc859ea-b100-46a7-a519-1c83f1bc8694)

## Features
* Use's `pyttsx3` engine to speak a selected message.
* Use's `pyperclip` to copy a message to clipboard.

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/ip-repo/ollama_st_app.git
    cd ollama_st_app
    ```

2. **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the Streamlit app:
```bash
streamlit run ollama_st_app.py
```

## Additional information
* The chat input is still usable while streaming a message or listening to the pyttsx3 engine speaking. This is a drawback and can allow the user to spam, resulting in unexpected behavior.
* In the file `ollama_st_app.py`, there is a list of `not_allowed_models`. This is to prevent the app from working with embedding models or other unsupported models like llava. You can update that list according to the models you have installed or simply avoid picking them from the select box in the app.
* Some models have a smaller context window than others, so it’s important to keep the chats relatively short. For example, one model might only be able to process 5 history messages, while another can handle up to 20 messages.
