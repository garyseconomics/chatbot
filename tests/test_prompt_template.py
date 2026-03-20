import langchain_core
from langchain_core.prompts import ChatPromptTemplate

from llm.prompt_template import get_rag_prompt


def test_prompt_template():
    prompt = get_rag_prompt()
    assert isinstance(prompt, ChatPromptTemplate)
    messages = prompt.invoke({"question": "Who are you?", "context": "You are an AI assistant."})
    assert isinstance(messages, langchain_core.prompt_values.ChatPromptValue)


def test_prompt_includes_current_datetime():
    prompt = get_rag_prompt()
    messages = prompt.invoke({"question": "What time is it?", "context": "No context."})
    rendered = messages.to_string()
    assert "Current date and time:" in rendered
    assert "UTC" in rendered
