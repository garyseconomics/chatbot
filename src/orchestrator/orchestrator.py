import logging

from langchain_core.messages import AIMessage, ToolMessage
from langfuse import observe

from config import settings
from knowledge.knowledge_manager import knowledge_to_text, store_new_knowledge
from llm.llm_manager import LLM_Client
from llm.prompt_template import get_chat_prompt, get_orchestrator_prompt
from orchestrator.tool_manager import call_tool, format_tool_result, get_tools_list
from orchestrator.tools_info import WRITE_ANSWER_TOOL_NAME

logger = logging.getLogger(__name__)


async def retrieve_info(conversation, knowledge, client_type) -> None:
    """The orchestrator AI: collect the information to answer the last question, and add it
    to the knowledge."""
    tools = await get_tools_list(client_type)
    orchestrator_ai = LLM_Client(tools=tools)
    # Initialize the orchestrator AI messages with the prompt
    messages = get_orchestrator_prompt(conversation, knowledge_to_text(knowledge))
    # Loop: the orchestrator AI calls tools until it calls write_answer (no cap for now)
    while True:
        response = await orchestrator_ai.chat(messages, user_id=None)
        # Fallback: a plain-text reply (no tool call) counts as write_answer
        if not response.tool_calls:
            return
        messages.append(response)
        for tool_call in response.tool_calls:
            if tool_call["name"] == WRITE_ANSWER_TOOL_NAME:
                return
            # The orchestrator AI writes the tool call's arguments (e.g. a search query)
            tool_result = await call_tool(tool_call["name"], tool_call["args"], client_type)
            store_new_knowledge(knowledge, tool_result)
            # The orchestrator AI sees what the tool found, to decide whether it has enough
            tool_message = format_tool_result(tool_result)
            messages.append(ToolMessage(content=tool_message, tool_call_id=tool_call["id"]))


async def generate_answer(conversation, knowledge) -> str:
    """The chat AI: write the answer to the last question in the conversation."""
    prompt = get_chat_prompt(conversation, knowledge_to_text(knowledge))
    response = await LLM_Client().chat(prompt, user_id=None)
    return response.content


@observe(
    name=settings.app_name,
    capture_input=settings.langfuse_message_tracing_enabled,
    capture_output=settings.langfuse_message_tracing_enabled,
)
async def answer_question(conversation, knowledge, client_type) -> str:
    """The orchestrator: answers the last question in the conversation, adds the answer to
    the conversation and stores the new knowledge retrieved."""
    try:
        await retrieve_info(conversation, knowledge, client_type)
        answer = await generate_answer(conversation, knowledge)
    except Exception as e:
        logger.error("Answering the question failed (%s): %s", type(e).__name__, e)
        # The error message is also kept, so the conversation is the same as the user sees it
        answer = settings.error_messages["DefaultError"]
    conversation.append(AIMessage(content=answer))
    return answer
