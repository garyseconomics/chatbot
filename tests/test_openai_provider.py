import pytest
from llm.llm_manager import LLM_Client
from langchain_ollama import ChatOllama
from config import settings

def test_get_chat_model_returns_ollama_for_ollama_type(monkeypatch):
    """If the provider type is 'ollama', get_chat_model() returns a ChatOllama instance."""
    always_reachable = staticmethod(lambda host, timeout=3.0: True)
    monkeypatch.setattr(LLM_Client, "_is_host_reachable", always_reachable)
    settings.chat_provider_priority = ["ollama_local"]
    client = LLM_Client()
    model = client.get_chat_model()
    assert isinstance(model, ChatOllama)