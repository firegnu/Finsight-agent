from openai import AsyncOpenAI

from ..config import settings


def make_client() -> AsyncOpenAI:
    """OpenAI-compatible async client. Points to LM Studio locally;
    week 2 can switch base_url to DeepSeek/Qwen online by changing .env only."""
    return AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )


llm = make_client()
MODEL = settings.llm_model
