def add_new_transcripts(knowledge, sources) -> dict:
    """Add to the knowledge only the transcripts it doesn't have yet."""
    if "transcripts" not in knowledge:
        knowledge["transcripts"] = []
    for source in sources:
        if source not in knowledge["transcripts"]:
            knowledge["transcripts"].append(source)
    return knowledge


def store_new_knowledge(knowledge, tool_result) -> dict:
    add_new_transcripts(knowledge, tool_result["sources"])
    return knowledge
