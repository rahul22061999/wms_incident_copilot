from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.caches import BaseCache
from langchain_ollama import ChatOllama
from config import settings



@lru_cache(maxsize=32)
def get_google_llm(cache: BaseCache | bool | None = None) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
            model=settings.GOOGLE_AI_MODEL,
            api_key=settings.GOOGLE_API_KEY,
            timeout=settings.GOOGLE_TIMEOUT,
            max_retries=0,
            cache=cache,
            temperature=0
        )



@lru_cache(maxsize=32)
def get_ollama_llm(cache: BaseCache | bool | None = None):
    return ChatOllama(
            model="gemma4:31b-cloud",
            base_url="http://localhost:11434",
            client_kwargs={
                "timeout": 100,   # seconds
                "headers": {
                    "Authorization": f"Bearer {settings.OLLAMA_API_KEY}"
                },
            },
        cache=cache,
        temperature=0
        )



@lru_cache(maxsize=32)
def get_openai_fast_llm(cache: BaseCache | bool | None = None):
    return ChatOpenAI(
            model=settings.OPEN_AI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
            cache=cache,
    )

@lru_cache(maxsize=32)
def get_groq_llm(cache: BaseCache | bool | None = None):
    return ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
        cache=cache,
        temperature=0
        )
