"""Azure OpenAI provider. Streaming responses, no content logging."""
from collections.abc import AsyncIterator

from openai import AsyncAzureOpenAI

from app.config import settings

# Reuse a single client to avoid httpx cleanup AttributeError (_state) when
# creating new clients per request.
_client_instance: AsyncAzureOpenAI | None = None


def _client() -> AsyncAzureOpenAI | None:
    """Return shared Azure OpenAI client if configured."""
    global _client_instance
    if not settings.azure_openai_configured:
        return None
    if _client_instance is None:
        _client_instance = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
    return _client_instance


async def stream_chat(
    *,
    system_prompt: str,
    messages: list[dict[str, str]],
    deployment: str | None = None,
) -> AsyncIterator[tuple[str | None, dict | None]]:
    """
    Stream chat completion from Azure OpenAI.
    Yields (text_chunk, None) for tokens, then (None, usage_dict) at end.
    """
    client = _client()
    if not client:
        raise RuntimeError("Azure OpenAI not configured")

    dep = deployment or settings.azure_openai_deployment
    all_messages: list[dict] = [{"role": "system", "content": system_prompt}]
    all_messages.extend(messages)

    stream = await client.chat.completions.create(
        model=dep,
        messages=all_messages,
        stream=True,
    )

    usage: dict = {"prompt_tokens": 0, "completion_tokens": 0}
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield (chunk.choices[0].delta.content, None)
        # usage exists only on final chunk; ChatCompletionChunk may not have it
        chunk_usage = getattr(chunk, "usage", None)
        if chunk_usage:
            usage = {
                "prompt_tokens": chunk_usage.prompt_tokens or 0,
                "completion_tokens": chunk_usage.completion_tokens or 0,
            }
    yield (None, usage)
