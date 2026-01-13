import os
from dotenv import load_dotenv
from langfuse import Langfuse, observe

class LangfuseManager:
	def __init__(self):
		self.langfuse_client = self.get_langfuse_client()

	def get_langfuse_client(self):
		load_dotenv()
		return Langfuse()

	def invoke(
		self,
		llm,
		prompt,
		model_name="",
		provider="ollama",
		user_id="carmen",
		app_name="GarysEconomics_bot",
	):
		if not app_name:
			app_name = os.getenv("LANGFUSE_APP_NAME", "GarysEconomics_bot")
		try:
			return self._invoke_observed(
				llm,
				prompt,
				model_name=model_name,
				provider=provider,
				user_id=user_id,
				app_name=app_name,
			)
		finally:
			self.langfuse_client.flush()

	@observe(name="ollama_request", as_type="generation", capture_input=True, capture_output=True)
	def _invoke_observed(self, llm, prompt, model_name="", provider="ollama", user_id="", app_name=""):
		self.langfuse_client.update_current_trace(
			name=app_name,
			user_id=user_id,
			metadata={"model": model_name, "provider": provider},
		)
		return llm.invoke(prompt)
