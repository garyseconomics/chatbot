import json
from typing_extensions import List, TypedDict
from langchain_core.documents import Document
from langgraph.graph import START, StateGraph
from llm.llm_manager import get_llm_client
from llm.prompt_template import get_rag_prompt
from vector_database.vector_database_manager import get_or_create_vector_database

# Load configuration 
with open('config.json', 'r') as f:
		config = json.load(f)
database_path = config['database_directory']


# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

# Define application steps
def retrieve(state: State):
    vector_store = get_or_create_vector_database(database_path)
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}

def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    prompt = get_rag_prompt()
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    print(f'\nPrompt generated:\n{messages}\n')
    llm = get_llm_client()
    response = llm.invoke(messages)
    return {"answer": response.content}

def RAG_query(question):
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()
    response = graph.invoke({"question": question})
    return response
