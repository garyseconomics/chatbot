from datetime import datetime, timezone

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from llm.prompt_versions import ORCHESTRATOR_PROMPT_TEXT, RAG_PROMPT_VERSIONS

RAG_PROMPT_TEXT = RAG_PROMPT_VERSIONS[settings.prompt_version]


def add_draft_to_context(knowledge, draft) -> str:
    prompt_context = list(knowledge.get("transcripts", []))
    # No draft when the RAG wasn't called in this turn
    if draft is not None:
        prompt_context.append(f"A draft answer written from the transcripts:\n{draft}")
    return "\n\n".join(prompt_context)


def prepare_orchestrator_prompt(conversation, knowledge) -> list:
    """Prepare the orchestrator AI's prompt: its instructions with the knowledge collected so
    far, then the conversation."""
    collected = "\n\n".join(knowledge.get("transcripts", []))
    instructions = SystemMessage(content=ORCHESTRATOR_PROMPT_TEXT.format(knowledge=collected))
    # A new list, so the tool calls added during the loop don't end up in the conversation
    return [instructions] + conversation


def get_rag_prompt():
    prompt = ChatPromptTemplate.from_messages([("human", RAG_PROMPT_TEXT)])
    # Checks if the prompt uses {current_datetime}
    if "{current_datetime}" in RAG_PROMPT_TEXT:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return prompt.partial(current_datetime=now)
    return prompt


def prepare_prompt_with_conversation(conversation, knowledge, draft) -> list:
    """Prepare the prompt with the conversation with the user."""
    last_message = conversation[-1].content
    prompt_context = add_draft_to_context(knowledge, draft)
    prompt = get_rag_prompt().format_messages(question=last_message, context=prompt_context)
    # The earlier turns go before the prompt as chat messages, so the model sees who said what.
    earlier_turns = conversation[:-1]
    prompt_with_conversation = earlier_turns + prompt
    return prompt_with_conversation
