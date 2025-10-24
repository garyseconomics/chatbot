import json
from langchain_community.document_loaders import SRTLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import chunk_size, chunk_overlap


def get_splits_from_srt(filename):
	# Load the content of the srt file
	loader = SRTLoader(filename)
	data = loader.load()

	# Split the document into parts
	splitter = RecursiveCharacterTextSplitter(
    	separators = ["\n\n", "\n", "."],
    	chunk_size = chunk_size,
    	chunk_overlap = chunk_overlap
	)

	all_splits = splitter.split_documents(data)
	return all_splits

