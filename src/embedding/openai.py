from langchain_openai import OpenAIEmbeddings

from src.config import settings
from src.embedding.base import EmbeddingBase


class OpenAIEmbedding(EmbeddingBase):
    """
    OpenAI embedding implementation using langchain_openai.

    Uses LITELLM_URL when set (e.g. for LiteLLM proxy), otherwise the default
    OpenAI API. Example: OpenAIEmbedding() for defaults, or
    OpenAIEmbedding(model="text-embedding-3-large") for a specific model.
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        **kwargs,
    ):
        self._model = OpenAIEmbeddings(
            model=model or settings.OPENAI_EMBEDDING_MODEL,
            api_key=api_key or settings.OPENAI_API_KEY or None,
            base_url=settings.LITELLM_URL,
            **kwargs,
        )

    @property
    def model(self) -> OpenAIEmbeddings:
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._model.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._model.aembed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return await self._model.aembed_query(text)
