def add_new_transcript_chunks(knowledge, transcript_chunks) -> dict:
    """Add to the knowledge only the transcript chunks it doesn't have yet."""
    if "transcript_chunks" not in knowledge:
        knowledge["transcript_chunks"] = []
    # Each chunk is {"video_id": ..., "text": ...}: it's new unless both are the same
    for chunk in transcript_chunks:
        if chunk not in knowledge["transcript_chunks"]:
            knowledge["transcript_chunks"].append(chunk)
    return knowledge


def store_new_knowledge(knowledge, tool_result) -> dict:
    add_new_transcript_chunks(knowledge, tool_result["transcript_chunks"])
    return knowledge
