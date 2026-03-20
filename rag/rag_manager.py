import logging

from langchain_core.documents import Document
from langfuse import observe
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict

from config import settings
from llm.llm_manager import LLM_Client
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
async def retrieve(state: State):
    vector_store = get_or_create_vector_database(settings.database_path)
    retrieved_docs = await vector_store.asimilarity_search(state["question"])
    return {"context": retrieved_docs}


async def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    prompt = get_rag_prompt()
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    logger.debug("Prompt generated:\n%s", messages)
    client = LLM_Client()
    response = await client.chat(messages, user_id=state["user_id"])
    return {"answer": response.content}


def build_error_state(e, question, user_id) -> State:
    error_type = type(e).__name__
    logger.error("RAG query failed (%s): %s", error_type, e)
    default_message = settings.error_messages["DefaultError"]
    return {
        "question": question,
        "user_id": user_id,
        "context": [],
        "answer": settings.error_messages.get(error_type, default_message),
    }


async def RAG_query(question, user_id) -> State:
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()
    try:
        # LangGraph's ainvoke: async version of invoke that doesn't block the event loop
        response = await graph.ainvoke({"question": question, "user_id": user_id})
        return response
    except Exception as e:
        return build_error_state(e, question, user_id)
