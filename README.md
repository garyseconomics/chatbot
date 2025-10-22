# Gary's Economics Chatbot 

A prototype chatbot designed to answer questions by referencing videos from Gary's Economics YouTube channel.

## Initial Setup

These are the instructions to run the project on an Ubuntu server.

1. **Open a Terminal and Execute the Following Commands:**

### Activate Virtual Environment
```bash
sudo apt-get update
sudo apt-get install python3-venv
python3 -m venv venv
source venv/bin/activate
```

### Install Python Libraries
```bash
pip install --upgrade pip
pip install pytest pysrt
```

### Install Langchain and its Dependencies
```bash
pip install -U langchain langchain_community langchain-ollama langchain_chroma langgraph
```

### Install Ollama and the Ollama Library for Python
```bash
sudo apt install curl
curl -fsSL https://ollama.com/install.sh | sh
pip install -U ollama
ollama pull llama3
```

## Testing
To execute the tests:
```bash
pytest
```