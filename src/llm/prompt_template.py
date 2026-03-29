from datetime import datetime, timezone

from langchain_core.prompts import ChatPromptTemplate

from config import settings
from llm.prompt_versions import RAG_PROMPT_VERSIONS

RAG_PROMPT_TEXT = RAG_PROMPT_VERSIONS[settings.prompt_version]


def get_rag_prompt():
    prompt = ChatPromptTemplate.from_messages([("human", RAG_PROMPT_TEXT)])
    # Checks if the prompt uses {current_datetime}
    if "{current_datetime}" in RAG_PROMPT_TEXT:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return prompt.partial(current_datetime=now)
    return prompt
