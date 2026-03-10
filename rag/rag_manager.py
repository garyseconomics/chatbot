import logging

from langchain_core.documents import Document
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict

from config import settings
from llm.llm_manager import llm_chat
from llm.prompt_template import get_rag_prompt
from vector_database.vector_database_manager import get_or_create_vector_database

logger = logging.getLogger(__name__)


# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


# Define application steps
def retrieve(state: State):
    vector_store = get_or_create_vector_database(settings.database_path)
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    prompt = get_rag_prompt()
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    logger.debug("Prompt generated:\n%s", messages)
    response = llm_chat(messages)
    return {"answer": response.content}


def RAG_query(question):
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()
    try:
        response = graph.invoke({"question": question})
        return response
    except Exception as e:
        logger.error("Failed while querying the RAG. Error: %s", e)
        return {"answer": "I'm sorry. I'm having some technical problems."}
