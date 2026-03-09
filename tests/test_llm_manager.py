import signal
import pytest
import langchain_core
from langchain_core.prompts import ChatPromptTemplate
from llm.llm_manager import get_llm_client, llm_chat
from llm.prompt_template import get_rag_prompt
from langchain_ollama import ChatOllama

test_model = "qwen3:4b"
REMOTE_TIMEOUT_SECONDS = 30


class RemoteTimeout(Exception):
    pass


def _on_timeout(signum, frame):
    raise RemoteTimeout("Remote Ollama timed out")


def llm_chat_with_fallback(timeout=REMOTE_TIMEOUT_SECONDS, **kwargs):
    """Try llm_chat with remote Ollama. If it times out, fall back to local."""
    signal.signal(signal.SIGALRM, _on_timeout)
    signal.alarm(timeout)
    try:
        return llm_chat(**kwargs)
    except RemoteTimeout:
        print(f"Remote timed out after {timeout}s, falling back to local Ollama")
        signal.alarm(0)
        llm = get_llm_client(force_local_llm=True)
        return llm_chat(llm=llm, **kwargs)
    finally:
        signal.alarm(0)


# --- Client creation tests (no network calls) ---

def test_get_llm_client_remote():
    llm = get_llm_client(force_local_llm=False)
    assert isinstance(llm, ChatOllama)


def test_get_llm_client_local():
    llm = get_llm_client(force_local_llm=True)
    assert isinstance(llm, ChatOllama)


def test_get_llm_with_model_name():
    llm = get_llm_client(force_local_llm=False, model_name=test_model)
    assert isinstance(llm, ChatOllama)


# --- Prompt template test (no network call) ---

def test_prompt_template():
    prompt = get_rag_prompt()
    assert isinstance(prompt, ChatPromptTemplate)
    messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
    assert isinstance(messages, langchain_core.prompt_values.ChatPromptValue)


# --- LLM chat tests (with remote timeout fallback to local) ---

def test_llm_chat_simple_prompt():
    response = llm_chat_with_fallback(prompt="Hello")
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


def test_llm_chat_with_prompt_template():
    prompt = ChatPromptTemplate.from_messages([("human", "Hello")])
    messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
    response = llm_chat_with_fallback(prompt=messages)
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


def test_llm_chat_with_model_name():
    response = llm_chat_with_fallback(prompt="Hello", model_name=test_model)
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


# --- Local-only test ---

def test_llm_chat_local():
    llm = get_llm_client(force_local_llm=True)
    response = llm_chat(prompt="Hello", llm=llm)
    assert isinstance(response, langchain_core.messages.ai.AIMessage)


# --- Remote-only test (must respond within 90 seconds or fail) ---

def test_llm_chat_remote():
    signal.signal(signal.SIGALRM, _on_timeout)
    signal.alarm(90)
    try:
        llm = get_llm_client(force_local_llm=False)
        response = llm_chat(prompt="Hello", llm=llm)
        assert isinstance(response, langchain_core.messages.ai.AIMessage)
    except RemoteTimeout:
        pytest.fail("Remote Ollama did not respond within 90 seconds")
    finally:
        signal.alarm(0)