from RAG_manager import RAG_query

print("This is the chatbot for Gary's Economics YouTube channel. You can ask me questions, and I will answer them using the content from our videos.")
question = input("Your question: ")
response = RAG_query(question)
print(response["answer"])
