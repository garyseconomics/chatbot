import os
from langchain_ollama import ChatOllama
from langfuse import Langfuse, observe
from dotenv import load_dotenv
from config import use_remote_llm, remote_llm, local_llm, provider, app_name
load_dotenv()


def get_llm_client(force_local_llm=False, model_name=""):
	# Uses the local Ollama when use_remote_llm in the config is set to False
	# or when this funtion is called with the parameter force_local_llm set to True
	if	force_local_llm or not use_remote_llm:
		# Using the local LLM
		if not model_name:
			model_name = local_llm
		ollama_host = os.getenv("OLLAMA_HOST_LOCAL", "http://localhost:11434")
		print(f"Using local LLM {model_name}")
		llm = ChatOllama(model=model_name, base_url=ollama_host)
		return llm
	else:
		# If use_remote_llm in config is set to True and force_local_llm is False,
		# connect with the remote ollama
		ollama_host = os.getenv("OLLAMA_HOST_REMOTE")
		# Calling remote LLM
		if not model_name:
			model_name = remote_llm
		print(f"Calling the remote LLM {model_name}")
		llm = ChatOllama(model=model_name, base_url=ollama_host)
		return llm

@observe(name="ollama_request", as_type="generation", capture_input=True, capture_output=True)
def llm_chat(prompt, llm=None, model_name="", user_id="not defined"):
	try:
		if not llm:
			llm = get_llm_client(force_local_llm=False, model_name=model_name)
		# Update langfuse trace
		langfuse_client = Langfuse()
		langfuse_client.update_current_trace(
			name = app_name,
			user_id = user_id,
			metadata={"model": model_name, "provider": provider},
		)
		# Calling the chat model with the prompt
		response = llm.invoke(prompt)
		return response
	except Exception as e:
		print(f"Failed to get response from LLM: {e}")
		llm = get_llm_client(force_local_llm=True, model_name=model_name)
		response = llm.invoke(prompt)
		return response
	finally:
		langfuse_client.flush()