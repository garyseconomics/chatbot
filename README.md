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

### Install Ollama and download the Llama 3 model 
```bash
sudo apt install curl
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
```

## Using this application
Open a terminal, go to the project directory and activate the virtual enviroment with this command:
```bash
source venv/bin/activate
```
### Load documents to the database
This application uses subtitles in srt format as information source. For the chatbot to be able to access this information it has to be imported to the database.
To import the documents, follow this steps:

- Select the subtitles in srt format that you want to import by moving them to the [docs folder](https://github.com/garyseconomics/chatbot/tree/main/docs).

> Note: All the documents in the docs folder will be imported, one after the other. This can take a while, so we advise that you try only with one subtitle on your first attemp, to get an idea of how long it'll take. Selecting files one by one to import is not implemented yet, but you can select the files by copying and deleting them from the docs folder before starting the regenerate database script. 


- Execute the regenerate database script.
```bash
python regenerate_database.py
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


### Testing
To execute the tests:
```bash
pytest
```
