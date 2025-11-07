import pytest
import langchain_core
from langchain_core.prompts import ChatPromptTemplate
from llm.llm_manager import *
from llm.prompt_template import get_rag_prompt

def test_get_llm_client_remote():
	llm = get_llm_client(force_local_llm=False)
	assert isinstance(llm,ChatOllama)

def test_get_llm_client_local():
	llm = get_llm_client(force_local_llm=True)
	assert isinstance(llm,ChatOllama)

def test_llm_chat_simple_prompt():
	response = llm_chat(prompt="Hello")
	assert isinstance(response, langchain_core.messages.ai.AIMessage)

def test_prompt_template():
	prompt = get_rag_prompt()
	assert isinstance(prompt, ChatPromptTemplate)
	messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
	assert isinstance(messages, langchain_core.prompt_values.ChatPromptValue)

def test_llm_chat_with_prompt_template():
	prompt = ChatPromptTemplate.from_messages([("human", "Hello")])
	messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
	response = llm_chat(messages)
	assert isinstance(response, langchain_core.messages.ai.AIMessage)

def test_llm_chat_local():
	llm = get_llm_client(force_local_llm=True)
	response = llm_chat(prompt="Hello", llm=llm)
	assert isinstance(response, langchain_core.messages.ai.AIMessage)
