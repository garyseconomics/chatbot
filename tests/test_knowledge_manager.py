from knowledge.knowledge_manager import store_new_knowledge


def test_store_new_knowledge_keeps_each_chunk_once_by_id():
    """Chunks are stored under their ID; a chunk that comes back in a later result isn't
    stored twice."""
    wealth_chunk = {"chunk_id": "id-1", "video_id": "v1", "text": "Wealth is..."}
    tax_chunk = {"chunk_id": "id-2", "video_id": "v2", "text": "A wealth tax is..."}
    first_result = {"database_id": "db-1", "transcript_chunks": [wealth_chunk]}
    second_result = {"database_id": "db-1", "transcript_chunks": [wealth_chunk, tax_chunk]}
    knowledge = {}

    store_new_knowledge(knowledge, first_result)
    store_new_knowledge(knowledge, second_result)

    assert knowledge["transcript_chunks"] == {
        "id-1": {"video_id": "v1", "text": "Wealth is..."},
        "id-2": {"video_id": "v2", "text": "A wealth tax is..."},
    }
