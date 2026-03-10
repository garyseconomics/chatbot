from unittest.mock import patch

import langchain_core
import pytest
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from config import settings
from llm import llm_manager
from llm.llm_manager import get_langfuse_client, get_llm_client, llm_chat
from llm.ollama_helpers import get_available_ollama_host
from llm.prompt_template import get_rag_prompt

# --- Ollama host fallback tests (mocked, no network calls) ---


def test_uses_remote_host_when_reachable():
    remote = "http://remote-server:11434"
    with (
        patch.object(settings, "ollama_host_remote", remote),
        patch("llm.ollama_helpers._is_host_reachable", return_value=True),
    ):
        host = get_available_ollama_host()
    assert host == remote


def test_falls_back_to_local_when_remote_unreachable():
    with patch("llm.ollama_helpers._is_host_reachable", return_value=False):
        host = get_available_ollama_host()
    assert host == settings.ollama_host_local


def test_falls_back_to_local_when_remote_not_configured():
    with patch.object(settings, "ollama_host_remote", ""):
        host = get_available_ollama_host()
    assert host == settings.ollama_host_local


def test_llm_client_uses_remote_model_when_remote_reachable():
    remote = "http://remote-server:11434"
    with (
        patch.object(settings, "ollama_host_remote", remote),
        patch("llm.ollama_helpers._is_host_reachable", return_value=True),
    ):
        llm = get_llm_client()
    assert llm.model == settings.remote_llm
    assert llm.base_url == remote


def test_llm_client_uses_local_model_when_remote_unreachable():
    with patch("llm.ollama_helpers._is_host_reachable", return_value=False):
        llm = get_llm_client()
    assert llm.model == settings.local_llm
    assert llm.base_url == settings.ollama_host_local


# --- Client creation tests (no network calls beyond the connectivity check) ---


def test_get_llm_client():
    llm = get_llm_client()
    assert isinstance(llm, ChatOllama)


def test_get_llm_client_with_model_name():
    llm = get_llm_client(model_name="qwen3:4b")
    assert isinstance(llm, ChatOllama)


# --- Prompt template test (no network call) ---


def test_prompt_template():
    prompt = get_rag_prompt()
    assert isinstance(prompt, ChatPromptTemplate)
    messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
    assert isinstance(messages, langchain_core.prompt_values.ChatPromptValue)


# --- LLM chat tests (uses best available host automatically) ---


def test_llm_chat_simple_prompt():
    response = llm_chat(prompt="Hello")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


def test_llm_chat_with_prompt_template():
    prompt = ChatPromptTemplate.from_messages([("human", "Hello")])
    messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
    response = llm_chat(prompt=messages)
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


def test_llm_chat_with_model_name():
    response = llm_chat(prompt="Hello", model_name="qwen3:4b")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


# --- Langfuse client tests (mocked, no network calls) ---


def test_langfuse_client_raises_when_credentials_missing():
    # Reset the cached client so get_langfuse_client() re-checks credentials
    original_client = llm_manager._langfuse_client
    llm_manager._langfuse_client = None
    try:
        with (
            patch.object(settings, "langfuse_public_key", ""),
            patch.object(settings, "langfuse_secret_key", ""),
        ):
            with pytest.raises(ValueError, match="Langfuse credentials are not configured"):
                get_langfuse_client()
    finally:
        llm_manager._langfuse_client = original_client
