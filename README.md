# Gary's Economics Chatbot 

A prototype chatbot designed to answer questions by referencing videos from Gary's Economics YouTube channel.

## Initial Setup

These are the instructions to run the project on an Ubuntu server. 
Open a terminal, go to the project directory and execute the following commands:

### Activate Virtual Environment
```bash
sudo apt-get update
sudo apt-get install python3-venv
python3 -m venv venv
source venv/bin/activate
```

### Install Libraries
```bash
pip install --upgrade pip
pip install -U pytest pysrt chromadb ollama
pip install -U langchain langchain_community langchain-ollama langchain_chroma langgraph
pip install -U python-telegram-bot

```

### Install Ollama and download the models
Before adding the documents to the vectorized database, they have to be processed with an embedding model. For this, we need to install Ollama in our server and then download the embedding model.
We are also using the local Ollama for the chat as backup in case the remote LLM fails.
```bash
sudo apt install curl
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3-embedding:8b
ollama pull llama3.2:3b
```
By default we are using the embedding model [Qwen3 8B](https://ollama.com/library/qwen3-embedding) and [Llama 3.2 3B](https://ollama.com/library/llama3.2:3b) for the chat.

You can select a diferent models by chaging the model name in config.py and downloading the new model with Ollama.
```bash
ollama pull model_name
```
Check the [Ollama library](https://ollama.com/library?sort=newest&q=embedding) for embedding models to use.

### Setting up the remote services
We have a file named .env that contains the secret keys to access the remote LLM, the Telegram and the Discord bots.

**IMPORTANT**: Because .env contain secret keys, we don't have it in the github repository. For the project to work you have to create your own .env file. To do this, make a copy of .env.sample naming it .env

In .env we have:
- OLLAMA_HOST: The url of the remote Ollama server (for the LLM we use for the chat).
- OLLAMA_API_KEY: We need this API key to connect to the remote Ollama server.
- TELEGRAM_TOKEN: This is used to connect with the Telegram bot. You receive the token when you [create a bot in Telegram using the BotFather](https://core.telegram.org/bots/tutorial#obtain-your-bot-token).
- DISCORD_TOKEN: This is used to connect with the Discord bot. For this you need a bot installed on a server with permission to read and send messages.

### Configuration
Anything that can be configured and is not on .env, it is in [config.py](https://github.com/garyseconomics/chatbot/blob/main/config.py)
- show_log: Select True if you want to see more information of what is happening on the terminal while you execute. False if not.
- use_remote_llm: By default is True. Change to False if you want to use always the local LLM.
- remote_llm: Name of the LLM in the remote server.
- local_llm: Name of the LLM in the local server (check the Ollama section for more information)
- embedding_model: The LLM we use to process the documents before importing them to the vectorized database.
- documents_directory: The folder where we have the subtitles before they are processed and imported to the database.
- database_path: The folder where we'll store the vectorized database (the database that contains the subtitles after they have been processed by the embedding).
- collection_name: The vectorized database store the documents in what they call "collections". You can choose other name for the collection, but change the name before importing the documents. Keep in mind that if you change the collection name after processing the documents, the chatbot won't be able to find the documents because it will be looking for them in the wrong collection.
- chunk_size: Before importing the subtitles into the database, we split them into smaller documents. The chunk size determines the size of those fragments. It is measured in "tokens" (basic units of text that LLMs use). We recommend 1024.
- chunk_overlap: This is the marging to cut the documents. We recommend a 20% of the chunk size.
- batch_size: The number of documents that we import to the database at the same time.
- video_ids_separator: We have put the youtube video ids at the begining of the srt files (we use that to get the links to the videos when the bot is answering the user). This sepparator is the characters we use to sepparate the video id ends from the name of the youtube video. Example: Q9VTje_FM08__Meritocracy.srt -> "Q9VTje_FM08" is the video id, "__" is the separator and "Meritocracy" is the title of the video. If you change this separator, you have to change the name of the files too or the video links won't work.
- discord_channel: Name of the channel in discord where the bot is configured to interact with the users.
- bot_greeting: The message that the bot will use to say hello when starting a conversation.


## Using this application
Open a terminal, go to the project directory and activate the virtual enviroment with this command:
```bash
source venv/bin/activate
```
### Import documents to the database
This application uses subtitles in srt format as information source. For the chatbot to be able to access this information it has to be imported to the database.
To import the documents, follow this steps:

- Select the subtitles in srt format that you want to import by moving them to the [docs/import folder](https://github.com/garyseconomics/chatbot/tree/main/docs).

> Note: All the documents in the import folder will be imported, one after the other. This can take a while, so we advise that you try only with one subtitle on your first attemp, to get an idea of how long it'll take. Selecting files one by one to import is not implemented yet, but you can select the files by moving them to the import folder before starting the regenerate database script.


- Execute the import documents script.
```bash
python import_documents.py
```
If documents have already been imported before, the script will ask you if you want to delete the collection. Answer "yes" only if you are sure you want to delete everything and start from scratch. Any answer except "yes" or "y" will skip this step and start importing the documents.

<img width="1862" height="532" alt="Image" src="https://github.com/user-attachments/assets/dde03966-f4b2-449c-8cf6-ced28b2cde1d" />

The script will show more information if logs are enabled. To turn the logs on and of, change the variable "show_logs" in config.py to True or False.


### Call the chatbot
To chat with the chatbot, execute the chatbot script:
```bash
python chatbot.py
```
The chatbot will greet you and ask you for a question. After providing the question, the chatbot will search for context in the database and answer you using the context it has find. The answers will be better when the subtitles already uploaded are related to the question asked.

<img width="1863" height="615" alt="Image" src="https://github.com/user-attachments/assets/7acdd1cb-0aa7-4137-8ad8-3d719fb13b3c" />

If logs are enabled, the chatbot will show you the prompt it has generated before calling to the LLM.


### Telegram chatbot
You can also access the chatbot through Telegram. To enable this, you have to start the telegram bot:
```bash
python telegram_bot.py
```
Then you can talk with the chatbot using this link to access the bot on Telegram: http://t.me/GarysEconomics_bot

### Discord chatbot
To run the bot in discord:
- Add the discord token to the .env file as DISCORD_TOKEN.
- Set the name of the channel on config.py in discord_channel.
- Launch the bot:
```bash
python discord_bot.py
```


### Testing
To execute the tests:
```bash
pytest
```