from datetime import datetime, timezone

from langchain_core.prompts import ChatPromptTemplate

from llm.prompt_versions import RAG_PROMPT_TEXT_V4

RAG_PROMPT_TEXT = RAG_PROMPT_TEXT_V4


def get_rag_prompt():
    prompt = ChatPromptTemplate.from_messages([("human", RAG_PROMPT_TEXT)])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return prompt.partial(current_datetime=now)
