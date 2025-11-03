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
	llm = get_llm_client()
	prompt = "Hello"
	response = llm_chat(llm, prompt)
	assert isinstance(response, langchain_core.messages.ai.AIMessage)

def test_prompt_template():
	prompt = get_rag_prompt()
	assert isinstance(prompt, ChatPromptTemplate)
	messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
	print(type(messages))
	assert isinstance(messages, langchain_core.prompt_values.ChatPromptValue)

def test_llm_chat_with_prompt_template():
    llm = get_llm_client()
    prompt = ChatPromptTemplate.from_messages([("human", "Hello")])
    messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
    response = llm_chat(llm, messages)
    assert isinstance(response, langchain_core.messages.ai.AIMessage)

def test_llm_chat_local():
	llm = get_llm_client(force_local_llm=True)
	prompt = "Hello"
	response = llm_chat(llm, prompt)
	assert isinstance(response, langchain_core.messages.ai.AIMessage)