import math
from typing import List, Sequence
from loguru import logger
import openai

from app.core.config import settings


class EmbeddingService:
    """Service for generating dense vector embeddings using OpenAI or fallback vector math."""

    EMBEDDING_MODEL = "text-embedding-3-small"

    @staticmethod
    async def get_embedding(text: str) -> List[float]:
        """Generate vector embedding for input text."""
        if not settings.OPENAI_API_KEY:
            return EmbeddingService._fallback_pseudo_embedding(text)

        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.embeddings.create(
                model=EmbeddingService.EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI Embedding API failed: {str(e)}. Falling back to pseudo vector generator.")
            return EmbeddingService._fallback_pseudo_embedding(text)

    @staticmethod
    def cosine_similarity(vec1: Sequence[float], vec2: Sequence[float]) -> float:
        """Calculate cosine similarity score between two dense vectors (range: 0.0 to 1.0)."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        similarity = dot_product / (norm_a * norm_b)
        return max(0.0, min(1.0, float(similarity)))

    @staticmethod
    def _fallback_pseudo_embedding(text: str, dim: int = 1536) -> List[float]:
        """Deterministic pseudo-random embedding generator for offline testing."""
        import hashlib
        text_clean = text.lower().strip()
        hash_seed = int(hashlib.md5(text_clean.encode("utf-8")).hexdigest(), 16)

        vec = []
        for i in range(dim):
            # Deterministic pseudo random float between -1.0 and 1.0
            val = math.sin((hash_seed + i) * 0.1)
            vec.append(val)

        # Normalize vector
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm > 0 else vec
