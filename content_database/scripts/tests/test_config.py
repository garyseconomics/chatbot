from content_database.config import settings


def test_vectorized_database_configuration():
    assert isinstance(settings.database_path, str)
    assert isinstance(settings.collection_name, str)
    assert isinstance(settings.chunk_size, int)
    assert isinstance(settings.chunk_overlap, int)
    assert isinstance(settings.batch_size, int)


def test_ollama_hosts():
    assert isinstance(settings.ollama_self_hosted_url, str)
    assert isinstance(settings.ollama_local_host_url, str)

