import logging

from langchain_core.documents import Document
from langfuse import observe
from langgraph.graph import START, StateGraph
from ollama import ResponseError
from typing_extensions import List, TypedDict

from config import settings
from llm.llm_manager import llm_chat
from llm.prompt_template import get_rag_prompt
from vector_database.vector_database_manager import get_or_create_vector_database

logger = logging.getLogger(__name__)


# Define state for application
class State(TypedDict):
    question: str
    user_id: str
    context: List[Document]
    answer: str


# Define application steps
@observe(name="vector_search")  # Track retrieval timing and results in Langfuse
def retrieve(state: State):
    vector_store = get_or_create_vector_database(settings.database_path)
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    prompt = get_rag_prompt()
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    logger.debug("Prompt generated:\n%s", messages)
    response = llm_chat(messages, user_id=state["user_id"])
    return {"answer": response.content}


def RAG_query(question: str, user_id: str = "unknown") -> State:
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()
    error_state: State = {
        "question": question,
        "user_id": user_id,
        "context": [],
        "answer": "I'm sorry. I'm having some technical problems.",
    }
    try:
        response = graph.invoke({"question": question, "user_id": user_id})
        return response
    except ConnectionError as e:
        logger.error("Cannot connect to Ollama: %s", e)
        error_state["answer"] = "I'm sorry, I can't reach the AI service right now."
        return error_state
    except ResponseError as e:
        logger.error("Ollama returned an error: %s", e)
        error_state["answer"] = "I'm sorry, the AI service returned an error."
        return error_state
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        error_state["answer"] = "I'm sorry, there's a configuration problem."
        return error_state
    except Exception as e:
        logger.error("Unexpected error while querying the RAG: %s", e)
        return error_state
