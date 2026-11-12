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
    prompt = ChatPromptTemplate.from_messages([("system", CHAT_PROMPT_TEXT)])
    # Checks if the prompt uses {current_datetime}
    if "{current_datetime}" in CHAT_PROMPT_TEXT:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return prompt.partial(current_datetime=now)
    return prompt


def get_chat_prompt(conversation, knowledge_text) -> list:
    """The chat AI's prompt: its instructions with the knowledge, then the conversation."""
    instructions = get_chat_prompt_template().format_messages(context=knowledge_text)
    # The conversation goes as it is, so the model sees who said what
    return instructions + conversation
