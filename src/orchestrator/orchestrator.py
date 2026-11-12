import logging

from langchain_core.messages import AIMessage, ToolMessage
from langfuse import observe

from config import settings
from knowledge.knowledge_manager import (
    knowledge_to_text,
    select_info_for_answer,
    store_new_knowledge,
)
from llm.llm_manager import LLM_Client
from llm.prompt_template import get_chat_prompt, get_orchestrator_prompt
from orchestrator.tool_manager import call_tool, format_tool_result, get_tools_list
from orchestrator.tools_info import SELECT_INFO_TOOL_NAME

logger = logging.getLogger(__name__)


async def retrieve_info(conversation, knowledge, client_type) -> dict:
    """The orchestrator AI: collect the information to answer the last question, add it to
    the knowledge, and return the information selected for the answer."""
    if not settings.max_tool_rounds:
        return select_info_for_answer(knowledge, {})
    tools = await get_tools_list(client_type)
    orchestrator_ai = LLM_Client(tools=tools)
    # Initialize the orchestrator AI messages with the prompt
    messages = get_orchestrator_prompt(conversation, knowledge_to_text(knowledge))
    # Loop: the orchestrator AI calls tools until it selects the info, or the cap is reached
    for _ in range(settings.max_tool_rounds):
        response = await orchestrator_ai.chat(messages, user_id=None)
        # Fallback: a plain-text reply (no tool call) ends the loop
        if not response.tool_calls:
            break
        messages.append(response)
        for tool_call in response.tool_calls:
            if tool_call["name"] == SELECT_INFO_TOOL_NAME:
                return select_info_for_answer(knowledge, tool_call["args"])
            # The orchestrator AI writes the tool call's arguments (e.g. a search query)
            tool_result = await call_tool(tool_call["name"], tool_call["args"], client_type)
            store_new_knowledge(knowledge, tool_result)
            # The orchestrator AI sees what the tool found, to decide whether it has enough
            tool_message = format_tool_result(tool_result)
            messages.append(ToolMessage(content=tool_message, tool_call_id=tool_call["id"]))
    else:
        logger.warning("Reached the cap of %d tool rounds", settings.max_tool_rounds)
    # The tool wasn't called: select the info anyway, from what was collected so far
    return select_info_for_answer(knowledge, {})


async def generate_answer(conversation, selected_info) -> str:
    """The chat AI: write the answer to the last question in the conversation."""
    prompt = get_chat_prompt(conversation, knowledge_to_text(selected_info))
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
        selected_info = await retrieve_info(conversation, knowledge, client_type)
        answer = await generate_answer(conversation, selected_info)
    except Exception as e:
        logger.error("Answering the question failed (%s): %s", type(e).__name__, e)
        # The error message is also kept, so the conversation is the same as the user sees it
        answer = settings.error_messages["DefaultError"]
    conversation.append(AIMessage(content=answer))
    return answer
