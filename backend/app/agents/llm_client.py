from openai import AsyncOpenAI

from app.config import settings


_client: AsyncOpenAI | None = None


def get_llm_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if settings.LLM_PROVIDER == "openai":
            _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            _client = AsyncOpenAI(
                api_key=settings.TENSORIX_API_KEY,
                base_url=settings.TENSORIX_BASE_URL,
            )
    return _client


async def complete(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: dict | None = None,
) -> str:
    client = get_llm_client()
    kwargs = dict(
        model=model or settings.TENSORIX_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if response_format:
        kwargs["response_format"] = response_format
    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content
