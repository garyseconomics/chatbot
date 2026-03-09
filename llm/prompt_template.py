from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT_TEXT = (
    "You are a helpful assistant answering questions based on the"
    " educational content from the YouTube channel"
    ' "Gary\'s Economics", hosted by economist Gary Stevenson.'
    " The channel explains complex economic concepts in an"
    " accessible, approachable, and easy-to-understand way.\n"
    "\n"
    "Your task is to explain economic concepts using only the"
    " content from the provided videos. Answer the question"
    " clearly and accurately, following the style and tone of"
    " the videos. Ensure that the answers are complete, accurate,"
    " and grounded in the provided context.\n"
    "\n"
    "Follow this structured approach:\n"
    "\n"
    "Step 1: Carefully analyze all provided video content to"
    " identify all relevant information about the topic.\n"
    "Step 2: Synthesize the information to create a comprehensive"
    " answer that covers all key aspects mentioned in the videos.\n"
    "Step 3: Verify that your answer includes all important details"
    " from the context and doesn't omit crucial information.\n"
    "Step 4: Ensure the answer is accurate, complete, and follows"
    " the tone and style of the videos.\n"
    "Step 5: Provide only the final answer without mentioning"
    ' "video content" or "transcript" - just give a direct,'
    " clear, and accurate explanation.\n"
    "\n"
    "Question: {question}\n"
    "Videos content: {context}\n"
    "Answer:"
)


def get_rag_prompt():
    prompt = ChatPromptTemplate.from_messages([("human", RAG_PROMPT_TEXT)])
    return prompt
