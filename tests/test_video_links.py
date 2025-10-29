import pytest
from langchain_core.documents.base import Document
from video_links import get_video_link


def test_get_video_link_when_no_documents():
    context = []
    video_link = get_video_link(context)
    assert video_link == ""


def test_get_video_link_1():
    filename = "docs/import/bReS9FLpgT4_MOOC_Part_1_What_Is_Wealth.srt"
    metadata = {"source": filename}
    doc = Document(metadata=metadata, page_content="")
    context = [doc]
    video_link = get_video_link(context)
    assert video_link == "https://www.youtube.com/watch?v=bReS9FLpgT4"

def test_get_video_link_2():
    filename = "docs/import/CivlU8hJVwc_MOOC_Part_3.srt"
    metadata = {"source": filename}
    doc = Document(metadata=metadata, page_content="")
    context = [doc]
    video_link = get_video_link(context)
    assert video_link == "https://www.youtube.com/watch?v=CivlU8hJVwc"