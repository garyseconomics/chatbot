import langchain_core
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from llm.prompt_template import get_chat_prompt, get_chat_prompt_template


def test_prompt_template_generates_a_chat_prompt():
    prompt = get_chat_prompt_template()
    assert isinstance(prompt, ChatPromptTemplate)
    messages = prompt.invoke({"context": "Wealth is ownership of assets."})
    assert isinstance(messages, langchain_core.prompt_values.ChatPromptValue)


def test_prompt_includes_current_datetime():
    prompt = get_chat_prompt_template()
    messages = prompt.invoke({"context": "No context."})
    rendered = messages.to_string()
    assert "Today is" in rendered
    assert "UTC" in rendered


def test_prompt_template_contains_the_knowledge():
    prompt = get_chat_prompt_template()
    assert isinstance(prompt, ChatPromptTemplate)
    knowledge_text = "Wealth is ownership of assets."
    messages = prompt.invoke({"context": knowledge_text})
    assert knowledge_text in messages.to_string()


def test_chat_prompt_keeps_the_conversation_after_the_instructions():
    """The instructions go in a system message with the knowledge; the conversation follows
    unchanged, so the model sees the user's last message as the user wrote it."""
    conversation = [
        HumanMessage(content="What is wealth?"),
        AIMessage(content="Wealth is ownership of assets."),
        HumanMessage(content="Tell me more"),
    ]

    prompt = get_chat_prompt(conversation, "Wealth is ownership of assets.")

    assert isinstance(prompt[0], SystemMessage)
    assert prompt[1:] == conversation
