"""Shared memory — a Chroma DB vector store all agents read from and write to.

Claims from every source are embedded with a local sentence-transformers model
(no API key, offline) so any step can semantically retrieve related claims
across sources — the basis for corroboration and conflict detection. Provenance
travels with each claim: the full `Claim` is serialized into metadata and
reconstructed on retrieval, so source/date/confidence survive the round-trip.

Production note: swap the local embedding function for a hosted embeddings
provider (e.g. Voyage AI) without changing the interface.
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
        self._client = chromadb.EphemeralClient(settings=Settings(anonymized_telemetry=False))
        embed: Any = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        # TODO: Create the collection. The in-process EphemeralClient caches one
        #   system per process, so a FIXED collection name collides across
        #   SharedMemory instances ("Collection already exists"). Give each
        #   instance a UNIQUE collection name, e.g. f"{COLLECTION}_{uuid.uuid4().hex}".
        self._collection: Any = None  # replace with self._client.create_collection(...)

    def add_claims(self, claims: list[Claim]) -> None:
        """Upsert claims; embeds claim+evidence, stores provenance as metadata."""
        if not claims:
            return
        # TODO: Build parallel lists of ids (_claim_id), documents (_document), and
        #   metadata, then self._collection.upsert(ids=, documents=, metadatas=).
        #   Chroma metadata values must be str/int/float/bool — None, lists, and
        #   tuples are rejected. Store source_date as an ISO string, and store the
        #   whole claim as JSON (c.model_dump_json()) so it can be rehydrated intact.
        raise NotImplementedError

    def _hydrate(self, metadatas: Any) -> list[Claim]:
        return [Claim.model_validate_json(str(m["claim_json"])) for m in metadatas]

    def search(self, query: str, k: int = 5) -> list[Claim]:
        """Return the k claims most semantically similar to `query`."""
        # TODO: Query the collection with query_texts=[query] and hydrate the
        #   returned metadatas back into Claims.
        raise NotImplementedError

    def related_to(self, claim: Claim, k: int = 5) -> list[Claim]:
        """Return claims similar to `claim`, excluding the claim itself."""
        # TODO: Query with the claim's document text, then drop the claim itself
        #   (match on _claim_id) before hydrating and returning up to k claims.
        raise NotImplementedError

    def count(self) -> int:
        return int(self._collection.count())
