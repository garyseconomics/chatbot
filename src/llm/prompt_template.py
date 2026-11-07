from datetime import datetime, timezone

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from llm.prompt_versions import CHAT_PROMPT_VERSIONS, ORCHESTRATOR_PROMPT_TEXT

CHAT_PROMPT_TEXT = CHAT_PROMPT_VERSIONS[settings.prompt_version]


def get_orchestrator_prompt(conversation, knowledge_text) -> list:
    """Prepare the orchestrator AI's prompt: its instructions with the knowledge collected so
    far, then the conversation."""
    instructions = SystemMessage(content=ORCHESTRATOR_PROMPT_TEXT.format(knowledge=knowledge_text))
    # A new list, so the tool calls added during the loop don't end up in the conversation
    return [instructions] + conversation


def get_chat_prompt_template() -> ChatPromptTemplate:
    prompt = ChatPromptTemplate.from_messages([("human", CHAT_PROMPT_TEXT)])
    # Checks if the prompt uses {current_datetime}
    if "{current_datetime}" in CHAT_PROMPT_TEXT:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return prompt.partial(current_datetime=now)
    return prompt


def get_chat_prompt(conversation, knowledge_text) -> list:
    """The chat AI's prompt: the previous messages of the conversation, then the instructions
    with the knowledge and the last message from the user."""
    last_message = conversation[-1].content
    prompt = get_chat_prompt_template().format_messages(
        question=last_message, context=knowledge_text
    )
    # The earlier turns go before the prompt as chat messages, so the model sees who said what.
    earlier_turns = conversation[:-1]
    prompt_with_conversation = earlier_turns + prompt
    return prompt_with_conversation
