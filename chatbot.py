from RAG_manager import RAG_query

question = "What is wealth?"
response = RAG_query(question)
print(response["answer"])
