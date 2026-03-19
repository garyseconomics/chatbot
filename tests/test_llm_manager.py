import langchain_core
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from llm.llm_manager import llm_chat
from llm.prompt_template import get_rag_prompt


def test_llm_chat_simple_prompt(use_ollama_for_testing):
    response = llm_chat(prompt="Hello")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


def test_prompt_template():
    prompt = get_rag_prompt()
    assert isinstance(prompt, ChatPromptTemplate)
    messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
    assert isinstance(messages, langchain_core.prompt_values.ChatPromptValue)


def test_llm_chat_with_prompt_template(use_ollama_for_testing):
    prompt = ChatPromptTemplate.from_messages([("human", "Hello")])
    messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
    response = llm_chat(messages)
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


def test_llm_chat_local_ollama():
    settings.chat_provider_priority = ["ollama_local"]
    response = llm_chat(prompt="Hello")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


def test_llm_chat_self_hosted_ollama():
    settings.chat_provider_priority = ["ollama_self_hosted"]
    response = llm_chat(prompt="Hello")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


def test_llm_chat_ollama_cloud():
    settings.chat_provider_priority = ["ollama_cloud"]
    response = llm_chat(prompt="Hello")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)
