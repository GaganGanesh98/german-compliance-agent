from langchain_groq import ChatGroq

from app.config import settings

GROQ_MODEL = "llama-3.3-70b-versatile"


def get_llm() -> ChatGroq:
    return ChatGroq(
        model=GROQ_MODEL,
        temperature=0,
        api_key=settings.groq_api_key,
    )
