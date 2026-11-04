import logging

from langchain_core.messages import AIMessage, ToolMessage
from langfuse import observe

from config import settings
from knowledge.knowledge_manager import store_new_knowledge
from knowledge.mcp_manager import call_tool, list_tools
from llm.llm_manager import LLM_Client
from llm.prompt_template import prepare_orchestrator_prompt, prepare_prompt_with_conversation
from llm.prompt_versions import WRITE_ANSWER_TOOL_DESCRIPTION, WRITE_ANSWER_TOOL_NAME

logger = logging.getLogger(__name__)

# Temporary: For now, the orchestrator AI can only call the RAG.
# We'll change this when we add more tools.
RAG_TOOL_NAME = "retrieval_augmented_generation"

# Handled by our own code, not the MCP server. It has no arguments.
WRITE_ANSWER_TOOL = {
    "name": WRITE_ANSWER_TOOL_NAME,
    "description": WRITE_ANSWER_TOOL_DESCRIPTION,
    "parameters": {"type": "object", "properties": {}},
}


async def get_orchestrator_tools(client_type) -> list[dict]:
    """The tools the orchestrator AI can call: the RAG, from the MCP server, and write_answer."""
    mcp_tools = await list_tools(client_type)
    rag_tools = [tool for tool in mcp_tools if tool["name"] == RAG_TOOL_NAME]
    return rag_tools + [WRITE_ANSWER_TOOL]


async def run_tool_call(tool_call, knowledge, client_type) -> str:
    """Run a tool call from the orchestrator AI on the MCP server, add the new transcripts to
    the knowledge, and return the RAG's draft."""
    # The orchestrator AI writes the query (the tool call's arguments)
    tool_result = await call_tool(tool_call["name"], tool_call["args"], client_type)
    store_new_knowledge(knowledge, tool_result)
    return tool_result["answer"]


async def retrieve_info(conversation, knowledge, client_type) -> str | None:
    """The orchestrator AI: collect the information to answer the last question, and add the
    new transcripts to the knowledge. Return the latest RAG draft of this turn, or None if the
    RAG wasn't called."""
    tools = await get_orchestrator_tools(client_type)
    orchestrator_ai = LLM_Client(tools=tools)
    messages = prepare_orchestrator_prompt(conversation, knowledge)
    draft = None
    # Loop: the orchestrator AI calls tools until it calls write_answer (no cap for now)
    while True:
        response = await orchestrator_ai.chat(messages, user_id=None)
        # Fallback: a plain-text reply (no tool call) counts as write_answer
        if not response.tool_calls:
            return draft
        messages.append(response)
        for tool_call in response.tool_calls:
            if tool_call["name"] == WRITE_ANSWER_TOOL_NAME:
                return draft
            draft = await run_tool_call(tool_call, knowledge, client_type)
            # The orchestrator AI sees the RAG's answer, to decide whether it has enough
            messages.append(ToolMessage(content=draft, tool_call_id=tool_call["id"]))


async def prepare_answer(conversation, knowledge, draft) -> str:
    """The chatbot AI: write the answer to the last question in the conversation."""
    prompt = prepare_prompt_with_conversation(conversation, knowledge, draft)
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
        draft = await retrieve_info(conversation, knowledge, client_type)
        answer = await prepare_answer(conversation, knowledge, draft)
    except Exception as e:
        logger.error("Answering the question failed (%s): %s", type(e).__name__, e)
        # The error message is also kept, so the conversation is the same as the user sees it
        answer = settings.error_messages["DefaultError"]
    conversation.append(AIMessage(content=answer))
    return answer
