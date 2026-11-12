# A tool handled by our own code, not the MCP server: the orchestrator AI calls it when it
# has enough information. It selects the information the chat AI gets to write the answer.
SELECT_INFO_TOOL_NAME = "select_info_for_answer"
SELECT_INFO_TOOL_DESCRIPTION = (
    "Select the information collected that the answer needs, and hand"
    " over to the chatbot, which writes the answer for the user. Call it"
    " when no more information is needed."
)
# It has no arguments for now.
SELECT_INFO_TOOL = {
    "name": SELECT_INFO_TOOL_NAME,
    "description": SELECT_INFO_TOOL_DESCRIPTION,
    "parameters": {"type": "object", "properties": {}},
}

# MCP tools the orchestrator AI doesn't get (the RAG: the chat AI writes the answer)
EXCLUDED_TOOL_NAMES = ["retrieval_augmented_generation"]

# The keys of the MCP tools' results that we know how to read (MCP_server#26: the same key
# always holds the same type of content). More keys will come with the new tools.
KNOWN_RESULT_KEYS = ["transcript_chunks"]
