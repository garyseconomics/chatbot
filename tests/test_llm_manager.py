import pytest
import langchain_core
from llm.llm_manager import *

def test_get_llm_client():
	llm = get_llm_client()
	assert isinstance(llm,ChatOllama)

def test_llm_chat_simple_prompt():
	llm = get_llm_client()
	prompt = "Hello"
	response = llm_chat(llm, prompt)
	assert isinstance(response, langchain_core.messages.ai.AIMessage)

