from rag.RAG_manager import RAG_query
from questions import questions_list

results = []
for question in questions_list:
	print(f"Question: {question}")
	response = RAG_query(question)
	print(f"Answer: {response}")
	results.append({"question": question, "answer": response["answer"]})

print(f"RESULTS:\n{results}")
