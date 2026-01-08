import os
from dotenv import load_dotenv
from langfuse import Langfuse, observe
from config import remote_llm

class LangfuseManager:
	def __init__(self):
		langfuse_client = self.get_langfuse_client()
		trace = None
		span = None

	def get_langfuse_client(self):
		load_dotenv()
		langfuse_client = Langfuse()
		return langfuse_client

	@observe(name="ollama_request", capture_input=True, capture_output=True)
	def trace(self, prompt):
		self.trace = self.langfuse_client.trace(
			name="GarysEconomics_bot",
			user_id="carmen",
			metadata={"model": remote_llm, "provider": "ollama"},
		)

		self.span = self.trace.span(
			name="llm-call",
			input={"prompt": prompt},
		)
		
	def end(self, response):
		self.span.end(output={"response": response})
		self.langfuse_client.flush()

