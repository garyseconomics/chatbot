import os
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

def get_llm_client():
	# Load environment variables
	load_dotenv()
	OLLAMA_HOST = os.getenv("OLLAMA_HOST")
	OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

	print(f"Connecting to host: {OLLAMA_HOST}")

	# Initialize LangChain with OpenAI API
	print("Calling the model")
	llm = ChatOllama(model="mistral-small3.1:24b", 
		api_key=OLLAMA_API_KEY,
		base_url=OLLAMA_HOST)
	return llm

def llm_chat(llm, prompt):
	try:
	    response = llm.invoke(prompt)
	    print("Response:", response)
	except Exception as e:
	    print(f"Failed to get response: {e}")

