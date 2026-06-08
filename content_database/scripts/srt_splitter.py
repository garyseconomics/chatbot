import pysrt
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from content_database.config import settings


def get_splits_from_srt(filename):
    # Load the content of the srt file
    parsed_info = pysrt.open(str(filename))
    # Replace langchain community's wrapper with the direct equivalent: 
    # https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/document_loaders/srt.py
    text = " ".join([sub.text for sub in parsed_info])
    data = [Document(page_content=text, metadata={"source": str(filename)})]

    # Split the document into parts
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "."],
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    all_splits = splitter.split_documents(data)
    return all_splits
