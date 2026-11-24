"""교체 가능한 임베딩 연결. 기본 예시는 외부 호출 없는 흐름 검증용이다."""

import hashlib
from importlib.metadata import version
import json
import math
import os
from typing import Protocol


class EmbeddingProvider(Protocol):
    # 모델, 차원, 전처리 등 벡터에 영향을 주는 설정이 바뀌면 identity도 바꾼다.
    identity: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class DemoHashEmbeddings:
    """문자 쌍을 해시한 결정적 데모 벡터. 의미 검색 품질 평가에 사용하지 않는다."""

    def __init__(self, dimensions: int = 64):
        if type(dimensions) is not int or dimensions < 1:
            raise ValueError("dimensions는 양의 정수여야 합니다.")
        self.dimensions = dimensions
        self.identity = (
            f"demo-hash-character-bigrams-v1:dimensions={dimensions}"
            ":casefold=1:whitespace=collapse:normalization=l2"
        )

    def embed_query(self, text: str) -> list[float]:
        text = " ".join(text.casefold().split())
        vector = [0.0] * self.dimensions
        parts = [text] if len(text) < 2 else [text[i:i + 2] for i in range(len(text) - 1)]
        for part in parts:
            if part:
                bucket = int.from_bytes(hashlib.sha256(part.encode()).digest()[:8])
                vector[bucket % self.dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]


class LangChainEmbeddingsAdapter:
    """이미 설정한 LangChain 임베더를 주입한다. 생성만으로 요청하지 않는다."""

    def __init__(self, client, identity: str):
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError("모델과 설정을 구분하는 identity가 필요합니다.")
        self.client = client
        self.identity = identity

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.client.embed_query(text)


def create_openai_embeddings(
    model: str, dimensions: int | None = None
) -> LangChainEmbeddingsAdapter:
    """호출자가 모델을 선택한 경우만 생성. API 키는 라이브러리가 환경에서 읽는다."""
    if not isinstance(model, str) or not model.strip():
        raise ValueError("OpenAI 임베딩 모델을 명시해야 합니다.")
    if dimensions is not None and (type(dimensions) is not int or dimensions < 1):
        raise ValueError("dimensions는 양의 정수여야 합니다.")
    from langchain_openai import OpenAIEmbeddings

    client = OpenAIEmbeddings(model=model, dimensions=dimensions)
    identity = json.dumps(
        {"provider": "openai", "model": model, "dimensions": dimensions,
         "base_url": client.openai_api_base or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
         "adapter": "langchain-openai:" + version("langchain-openai")},
        sort_keys=True, ensure_ascii=False,
    )
    return LangChainEmbeddingsAdapter(client, identity)
