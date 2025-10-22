import json
import pytest
from langchain_core.documents.base import Document
from vector_database.srt_splitter import get_splits_from_srt

# Read the configuration from config.json
with open('config.json', 'r') as f:
    config = json.load(f)

def test_chunks_config():
    assert isinstance(config['chunk_size'], int)
    assert isinstance(config['chunk_overlap'], int)

@pytest.fixture
def sample_srt_file():
    """Fixture to return the path of a sample SRT file for testing."""
    return "tests/sample.srt"

def test_get_splits_from_srt(sample_srt_file):
    # Call the function that splits the SRT document
    all_splits = get_splits_from_srt(sample_srt_file)

    # Ensure the number of splits is within a reasonable range 
    assert len(all_splits) <= config['chunk_size'] * 2

    # test that returns a document
    assert isinstance(all_splits[0], Document)

     # test a fragment
    expected_content = '''Okay. Welcome back to Gary’s Economics. Today we are going to introduce the first part of our online course. Video number one, which is going to be What is Wealth. Okay so I was at a conference the other day, a conference about economics media, and there was a guy who basically spoke about how when'''
    assert all_splits[0].page_content == expected_content
