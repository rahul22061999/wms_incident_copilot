from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from openai import max_retries
from langchain_ollama import ChatOllama

from config import settings


_gemini_llm = None
@lru_cache(maxsize=1)
def get_google_llm():
    global _gemini_llm
    if _gemini_llm is None:
        _gemini_llm = ChatGoogleGenerativeAI(
            model=settings.GOOGLE_AI_MODEL,
            api_key=settings.GOOGLE_API_KEY,
            timeout=settings.GOOGLE_TIMEOUT,
            max_retries=0
        )
    return _gemini_llm


_ollama_llm =None
@lru_cache(maxsize=1)
def get_ollama_llm():
    global _ollama_llm
    if _ollama_llm is None:
        _ollama_llm = ChatOllama(
            model="gemma4:31b-cloud",
            base_url="http://localhost:11434",
            client_kwargs={
                "timeout": 5.0,   # seconds
                "headers": {
                    "Authorization": f"Bearer {settings.OLLAMA_API_KEY}"
                },
            },
        )
    return _ollama_llm


_openai_fast_llm = None
def get_openai_fast_llm():
    global _openai_fast_llm
    if _openai_fast_llm is None:
        _openai_fast_llm = ChatOpenAI(
            model=settings.OPEN_AI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0

        )
    return _openai_fast_llm

_groq_llm = None
def get_groq_llm():
    global _groq_llm
    if _groq_llm is None:
        _groq_llm = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
        )
    return _groq_llm