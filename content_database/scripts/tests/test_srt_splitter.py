import pytest
from langchain_core.documents.base import Document

from content_database.config import settings
from content_database.scripts.srt_splitter import get_splits_from_srt


@pytest.fixture
def sample_srt_file():
    """Fixture to return the path of a sample SRT file for testing."""
    return "content_database/scripts/tests/sample.srt"


def test_get_splits_from_srt(sample_srt_file):
    all_splits = get_splits_from_srt(sample_srt_file)

    assert len(all_splits) >= 1
    assert isinstance(all_splits[0], Document)

    content = all_splits[0].page_content
    assert content.startswith("Okay. Welcome back to Gary")
    assert "What is Wealth" in content
    assert content.endswith("they watch it through.")


def test_all_splits_are_documents(sample_srt_file):
    all_splits = get_splits_from_srt(sample_srt_file)
    for split in all_splits:
        assert isinstance(split, Document)


def test_splits_have_source_metadata(sample_srt_file):
    all_splits = get_splits_from_srt(sample_srt_file)
    for split in all_splits:
        assert "source" in split.metadata
        assert split.metadata["source"] == sample_srt_file


def test_splits_respect_chunk_size(sample_srt_file):
    all_splits = get_splits_from_srt(sample_srt_file)
    for split in all_splits:
        assert len(split.page_content) <= settings.chunk_size
