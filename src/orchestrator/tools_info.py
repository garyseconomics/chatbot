# A tool handled by our own code, not the MCP server: the orchestrator AI calls it to hand
# over to the chat AI, which writes the answer.
WRITE_ANSWER_TOOL_NAME = "write_answer"
WRITE_ANSWER_TOOL_DESCRIPTION = (
    "Hand over to the chatbot, which writes the answer for the user"
    " from the conversation and the information collected. Call it"
    " when no more information is needed."
)
# It has no arguments.
WRITE_ANSWER_TOOL = {
    "name": WRITE_ANSWER_TOOL_NAME,
    "description": WRITE_ANSWER_TOOL_DESCRIPTION,
    "parameters": {"type": "object", "properties": {}},
}

# MCP tools the orchestrator AI doesn't get (the RAG: the chat AI writes the answer)
EXCLUDED_TOOL_NAMES = ["retrieval_augmented_generation"]
