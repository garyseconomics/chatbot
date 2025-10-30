import pytest
from langchain_core.documents.base import Document
from video_links import get_video_link, videos_text_for_chat

# Testing examples
video1 = "https://www.youtube.com/watch?v=bReS9FLpgT4"
video2 = "https://www.youtube.com/watch?v=CivlU8hJVwc"
filename1 = "docs/import/bReS9FLpgT4_MOOC_Part_1_What_Is_Wealth.srt"
filename2 = "docs/import/CivlU8hJVwc_MOOC_Part_3.srt"
doc1 = Document(metadata={"source": "docs/import/bReS9FLpgT4_MOOC_Part_1_What_Is_Wealth.srt"}, page_content="")
doc2 = Document(metadata={"source": "docs/import/CivlU8hJVwc_MOOC_Part_3.srt"}, page_content="")


def test_get_video_link_when_no_documents():
    context = []
    video_link = get_video_link(context)
    assert video_link == []

def test_get_video_link_1():
    context = [doc1]
    video_link = get_video_link(context)
    assert video_link == [video1]

def test_get_video_link_2():
    context = [doc2]
    video_link = get_video_link(context)
    assert video_link == [video2]

def test_get_video_link_several_videos():
    context = [doc1, doc2, doc1]
    video_link = get_video_link(context)
    assert video_link == [video1, video2]

def test_videos_text_for_chat_no_videos():
    video_links = []
    videos_text = videos_text_for_chat(video_links)
    assert videos_text == ""

def test_videos_text_for_chat_1_video():
    video_links = [video1]
    videos_text = videos_text_for_chat(video_links)
    assert videos_text == f"More information on this video: {video1}"

def test_videos_text_for_chat_several_videos():
    video_links = [video1, video2]
    videos_text = videos_text_for_chat(video_links)
    assert videos_text == f"More information on this videos:\n{video1}\n{video2}\n"