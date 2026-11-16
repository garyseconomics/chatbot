def add_new_transcript_chunks(knowledge, transcript_chunks) -> dict:
    """Add to the knowledge only the transcript chunks it doesn't have yet."""
    if "transcript_chunks" not in knowledge:
        knowledge["transcript_chunks"] = {}
    # Stored by their chunk ID in the MCP database: {chunk_id: {"video_id": ..., "text": ...}}
    for chunk in transcript_chunks:
        if chunk["chunk_id"] not in knowledge["transcript_chunks"]:
            knowledge["transcript_chunks"][chunk["chunk_id"]] = {
                "video_id": chunk["video_id"],
                "text": chunk["text"],
            }
    return knowledge


def store_new_knowledge(knowledge, tool_result) -> dict:
    """Store the parts of a tool result the knowledge knows; ignore the rest."""
    if "transcript_chunks" in tool_result:
        add_new_transcript_chunks(knowledge, tool_result["transcript_chunks"])
    return knowledge


def knowledge_to_text(knowledge) -> str:
    """The knowledge as text, for the LLMs' prompts."""
    # Only the text goes to the LLMs for now, not the video_id
    chunk_texts = [chunk["text"] for chunk in knowledge.get("transcript_chunks", {}).values()]
    return "\n\n".join(chunk_texts)


def select_info_for_answer(knowledge, arguments) -> dict:
    """The information the chat AI gets to write the answer. For now, all the knowledge."""
    return dict(knowledge)
