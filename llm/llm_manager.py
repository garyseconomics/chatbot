import os
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from config import use_remote_llm, remote_llm, local_llm


def get_llm_client(force_local_llm=False):
	# Uses the local Ollama when use_remote_llm in the config is set to False
	# or when this funtion is called with the parameter force_local_llm set to True
	if	force_local_llm or not use_remote_llm:
		# Using the local LLM
		print(f"Using local LLM {local_llm}")
		llm = ChatOllama(model=local_llm)
		return llm
	else:
		# If use_remote_llm in config is set to True and force_local_llm is False,
		# connect with the remote ollama

		# Load the ollama host and the API key from the environment variables
		load_dotenv()
		OLLAMA_HOST = os.getenv("OLLAMA_HOST")
		OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
		# Calling remote LLM
		print(f"Calling the remote LLM {remote_llm}")
		llm = ChatOllama(model=remote_llm,
			api_key=OLLAMA_API_KEY,
			base_url=OLLAMA_HOST)
		return llm

def llm_chat(prompt, llm=None):
	try:
		if not llm:
			llm = get_llm_client(force_local_llm=False)
		response = llm.invoke(prompt)
		return response
	except Exception as e:
		print(f"Failed to get response from LLM: {e}")
		llm = get_llm_client(force_local_llm=True)
		response = llm.invoke(prompt)
		return response
