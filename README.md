# Gary's Economics Chatbot 

A prototype chatbot designed to answer questions by referencing videos from Gary's Economics YouTube channel.

## Setup with Docker
Note: This instructions asume you are on an Ubuntu server. 

### Configure the enviroment variables
Make a copy of the file named [.env.sample](https://github.com/garyseconomics/chatbot/blob/main/.env.sample), naming it .env. In this file you have to configure the information of your API keys to access diferent services.
For more information about each of the content of this file, consult the section [setting-up-the-remote-services](https://github.com/garyseconomics/chatbot/tree/main?tab=readme-ov-file#setting-up-the-remote-services).

### Include a copy of the database
To run the application you need a copy of the vectorized dabase with the subtitles. You can use a copy of the database (recomended) or you can create your own.

Using a copy: 
- Download a copy of "chroma.sqlite3" from [this repository]( https://github.com/garyseconomics/chatbot-database)
- Create a folder named "chroma_langchain_db" in the "vectorized_database" folder.
- Move chroma.sqlite3 to the chroma_langchain_db folder. 

The path of the file should be:
```bash
chatbot/vector_database/chroma_langchain_db/chroma.sqlite3
```

Alternativately, you can generate your own database following the steps on the [Import documents to the database section](https://github.com/garyseconomics/chatbot?tab=readme-ov-file#import-documents-to-the-database).

### Build the docker container
Build the docker container executing this command while you are in the chatbot folder:
```bash
docker compose build
```
### Run the docker container
Once you have build the container, run it using this command:
```bash
docker compose up
```
Or, if you want the service to restart automatically:
```bash
docker compose up -d
```
This will put the docker image running on the background. 

## Setup without Docker

Note: This instructions asume you are on an Ubuntu server.

Open a terminal, go to the project directory and execute the following commands:

### Create virtual environment and install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```
This reads `pyproject.toml` and installs all dependencies. To also install development tools (ruff, pytest):
```bash
pip install ".[dev]"
```

### Install Ollama and download the models
In our application we use one type of AIs called Large Language Models (LLM or model for short). We use them for two things:

**1. Processing the subtitles before adding them to the vectorized database:**

The process that the AI does here is called [embedding](https://en.wikipedia.org/wiki/Embedding_(machine_learning)) or vectorization. It identifies concepts in the documents and create "vectors", that are numerical representation of this concepts. This will be used later to find related concepts when searching the database.

For this task we have by default configured an LLM called [Qwen3-embedding](https://ollama.com/library/qwen3-embedding) that is specially trained for this, and we have opted to install it locally, in our own server. To run the model in our server we need to install Ollama and then download the embedding model.
```bash
sudo apt install curl
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3-embedding:8b
```
You can select a diferent model by chaging `embedding_model` in [config.py](https://github.com/garyseconomics/chatbot/blob/main/config.py) and downloading the new model with Ollama.
```bash
ollama pull model_name
```
Check the [Ollama library](https://ollama.com/library?sort=newest&q=embedding) for embedding models to use.

**2. Answering the users questions:**

By default we are using an LLM in a remote server for this task. How to set up the remote LLM is explained in the next section [Setting up the remote services](https://github.com/garyseconomics/chatbot/edit/main/README.md#setting-up-the-remote-services).

We are also using the local Ollama for the chat as backup in case the remote LLM fails. The local LLM we are using by default for the chat is [Llama 3.2 3B](https://ollama.com/library/llama3.2:3b). Install it with this command:
```bash
ollama pull llama3.2:3b
```
The chatbot automatically checks if the remote Ollama is reachable and falls back to the local one if it's not. This applies to both chat and embeddings.
You can install a diferent model for the chat by downloading that model with Ollama and changing `local_llm` in [config.py](https://github.com/garyseconomics/chatbot/blob/main/config.py).

### Setting up the remote services
We have a file named .env that contains the secret keys to access the remote LLM, the Telegram and the Discord bots.

**IMPORTANT**: Because .env contain secret keys, we don't have it in the github repository. For the project to work you have to create your own .env file. To do this, make a copy of [.env.sample](https://github.com/garyseconomics/chatbot/blob/main/.env.sample) naming it .env

In .env we have:
- OLLAMA_HOST_LOCAL: The url of the local Ollama server. Defaults to `http://localhost:11434`.
- OLLAMA_HOST_REMOTE: The url of the remote Ollama server.
- OLLAMA_API_KEY: API key to connect to the remote Ollama server.
- TELEGRAM_TOKEN: This is used to connect with the Telegram bot. You receive the token when you [create a bot in Telegram using the BotFather](https://github.com/garyseconomics/chatbot/edit/main/README.md#telegram-chatbot).
- DISCORD_TOKEN: This is used to connect with the Discord bot. For this you need a bot installed on a server with permission to read and send messages.
- LANGFUSE_PUBLIC_KEY: Public key for the Langfuse observability platform.
- LANGFUSE_SECRET_KEY: Secret key for Langfuse.
- LANGFUSE_HOST: Langfuse server URL. Defaults to `https://cloud.langfuse.com`.

<img width="729" height="166" alt="Image" src="https://github.com/user-attachments/assets/154a1e8f-335f-4de9-b085-20c8cb57b419" />

### Configuration
All configuration is managed in [config.py](https://github.com/garyseconomics/chatbot/blob/main/config.py) through a `Settings` class (using [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)). Environment variables from `.env` are loaded automatically — each field in the class maps to an env var of the same name. Fields that are not set in `.env` use the default values defined in the class.

Available settings:

**LLM settings**
- **remote_llm**: Name of the LLM in the remote server.
- **local_llm**: Name of the LLM in the local server. Check the [Ollama section](https://github.com/garyseconomics/chatbot/edit/main/README.md#install-ollama-and-download-the-models) for more information.
- **embedding_model**: The LLM we use to process the documents before importing them to the vectorized database.

**Vector database**
- **database_path**: The folder where we'll store the vectorized database (the database that contains the subtitles after they have been processed by the embedding).
- **collection_name**: The vectorized database store the documents in what they call "collections". You can choose other name for the collection, but change the name before importing the documents. Keep in mind that if you change the collection name after processing the documents, the chatbot won't be able to find the documents because it will be looking for them in the wrong collection.
- **chunk_size**: Before importing the subtitles into the database, we split them into smaller documents. The chunk size determines the size of those fragments. It is measured in ["tokens"](https://en.wikipedia.org/wiki/Large_language_model#Tokenization) (basic units of text that LLMs use). We recommend 1024.
- **chunk_overlap**: This is the marging to cut the documents. We recommend a 20% of the chunk size.
- **batch_size**: The number of documents that we import to the database at the same time.

**Documents**
- **documents_directory**: The folder where we have the subtitles before they are processed and imported to the database.
- **video_ids_separator**: We have put the youtube video ids at the begining of the srt files (we use that to get the links to the videos when the bot is answering the user). This sepparator is the characters we use to sepparate the video id ends from the name of the youtube video. Example: Q9VTje_FM08__Meritocracy.srt -> "Q9VTje_FM08" is the video id, "__" is the separator and "Meritocracy" is the title of the video. If you change this separator, you have to change the name of the files too or the video links won't work.

**App**
- **show_logs**: Select True if you want to see more information of what is happening on the terminal while you execute. False if not.
- **bot_greeting**: The message that the bot will use to say hello when starting a conversation.
- **discord_channel**: Name of the channel in discord where the bot is configured to interact with the users.


## Using this application
Open a terminal, go to the project directory and activate the virtual environment with this command:
```bash
source .venv/bin/activate
```
### Import documents to the database
This application uses subtitles in srt format as information source. For the chatbot to be able to access this information it has to be imported to the database.
To import the documents, follow this steps:

- Select the subtitles in srt format that you want to import by moving them to the [docs/import folder](https://github.com/garyseconomics/chatbot/tree/main/docs).

> Note: All the documents in the import folder will be imported, one after the other. This can take a while, so we advise that you try only with one subtitle on your first attemp, to get an idea of how long it'll take. Selecting files one by one to import is not implemented yet, but you can select the files by moving them to the import folder before starting the regenerate database script.


- Execute the import documents script.
```bash
python -m vector_database.import_documents
```
If documents have already been imported before, the script will ask you if you want to delete the collection. Answer "yes" only if you are sure you want to delete everything and start from scratch. Any answer except "yes" or "y" will skip this step and start importing the documents.

<img width="1862" height="532" alt="Image" src="https://github.com/user-attachments/assets/dde03966-f4b2-449c-8cf6-ced28b2cde1d" />

The script will show more information if logs are enabled. To turn the logs on and off, set `SHOW_LOGS` to `True` or `False` in your `.env` file (or change the default in `config.py`).


### Call the chatbot
To chat with the chatbot, execute the chatbot script:
```bash
python -m interfaces.chatbot
```
The chatbot will greet you and ask you for a question. After providing the question, the chatbot will search for context in the database and answer you using the context it has find. The answers will be better when the subtitles already uploaded are related to the question asked.

<img width="1863" height="615" alt="Image" src="https://github.com/user-attachments/assets/7acdd1cb-0aa7-4137-8ad8-3d719fb13b3c" />

If logs are enabled, the chatbot will show you the prompt it has generated before calling to the LLM.


### Telegram chatbot
You can also access the chatbot through Telegram. To enable this, first you need a Telegram bot.

**Create a Telegram bot**
- Go to the Telegram app. You can install the app in your phone. Also you can access using [this web](https://web.telegram.org/) (although it'll ask you to use the phone app to login).
- Open a conversation with @BotFather. Be careful here, because there are serveral BotFather doppelgangers. Ensure that it is the real one. It should have the blue checkmark and more than 3 million followers.
<img width="446" height="424" alt="Image" src="https://github.com/user-attachments/assets/dc86f1e5-a957-43d6-ba65-94ab377a26d5" />

- In the conversation with BotFather, write /newbot to create your bot. It will ask you to name your bot (this is the name people will see) and also to give it a "username" (that is an internal name that will be used in the url to access the bot). For example name: Garys Economics, username: GarysEconomics_bot. The BotFather will give you the url to access the bot (this is the link you can share with others so they can access the bot) and the token.
<img width="776" height="457" alt="Image" src="https://github.com/user-attachments/assets/1865122a-8d1d-462b-ad57-71aa12f5ae90" />

- Copy the token to the [.env file](https://github.com/garyseconomics/chatbot/edit/main/README.md#setting-up-the-remote-services).
<img width="729" height="166" alt="Image" src="https://github.com/user-attachments/assets/154a1e8f-335f-4de9-b085-20c8cb57b419" />

More information about Telegram bots in [this link](https://core.telegram.org/bots/tutorial#obtain-your-bot-token).


**Launch the telegram bot**
```bash
python -m interfaces.telegram_bot
```
Then you can talk with the chatbot using the link the BotFather gave you to access the bot on Telegram. For example: http://t.me/GarysEconomics_bot


### Discord chatbot
To run the bot in discord:
- Add the discord token to the .env file as DISCORD_TOKEN.
- Set the name of the channel as `DISCORD_CHANNEL` in your `.env` file (or change the default in `config.py`).
- Launch the bot:
```bash
python -m interfaces.discord_bot
```


### Testing
To execute the tests:
```bash
pytest
```
