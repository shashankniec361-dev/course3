
"""Shared memory — a Chroma DB vector store all agents read from and write to.

Claims from every source are embedded with a local sentence-transformers model
(no API key, offline) so any step can semantically retrieve related claims
across sources — the basis for corroboration and conflict detection. Provenance
travels with each claim: the full Claim is serialized into metadata and
reconstructed on retrieval, so source/date/confidence survive the round-trip.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Any

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from .models import Claim

EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION = "supply_chain_claims"


def _claim_id(claim: Claim) -> str:
    key = f"{claim.source}|{claim.metric_id}|{claim.claim}"
    return hashlib.sha1(key.encode()).hexdigest()


def _document(claim: Claim) -> str:
    return f"{claim.claim} {claim.evidence}"


class SharedMemory:
    """A Chroma-backed store of claims with semantic cross-source retrieval."""

    def __init__(self, embedding_model: str = EMBED_MODEL) -> None:
        self._client = chromadb.EphemeralClient(
            settings=Settings(anonymized_telemetry=False)
        )

        embed: Any = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )

        # Each instance gets its own collection to avoid collection-name
        # collisions between SharedMemory instances.
        collection_name = f"{COLLECTION}_{uuid.uuid4().hex}"

        self._collection: Any = self._client.create_collection(
            name=collection_name,
            embedding_function=embed,
            metadata={"description": "Supply-chain investigation claims"},
        )

    def add_claims(self, claims: list[Claim]) -> None:
        """Upsert claims and preserve their provenance as metadata."""
        if not claims:
            return

        ids = [_claim_id(claim) for claim in claims]
        documents = [_document(claim) for claim in claims]

        metadatas = [
            {
                "source": claim.source,
                "source_date": claim.source_date.isoformat(),
                "confidence": claim.confidence,
                "metric_id": claim.metric_id,
                "claim_json": claim.model_dump_json(),
            }
            for claim in claims
        ]

        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

    def _hydrate(self, metadatas: Any) -> list[Claim]:
        """Reconstruct Claim objects from Chroma metadata."""
        return [
            Claim.model_validate_json(str(metadata["claim_json"]))
            for metadata in metadatas
        ]

    def search(self, query: str, k: int = 5) -> list[Claim]:
        """Return the k claims most semantically similar to query."""
        if k <= 0 or self.count() == 0:
            return []

        result = self._collection.query(
            query_texts=[query],
            n_results=min(k, self.count()),
            include=["metadatas"],
        )

        metadatas = result.get("metadatas") or [[]]
        return self._hydrate(metadatas[0])

    def related_to(self, claim: Claim, k: int = 5) -> list[Claim]:
        """Return claims similar to claim, excluding the claim itself."""
        if k <= 0 or self.count() == 0:
            return []

        result = self._collection.query(
            query_texts=[_document(claim)],
            n_results=min(self.count(), k + 1),
            include=["metadatas"],
        )

        metadatas = result.get("metadatas") or [[]]
        related = self._hydrate(metadatas[0])

        claim_id = _claim_id(claim)

        return [
            candidate
            for candidate in related
            if _claim_id(candidate) != claim_id
        ][:k]

    def count(self) -> int:
        return int(self._collection.count())
