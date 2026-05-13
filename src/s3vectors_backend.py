"""S3 Vectors backend with the same surface as the Qdrant path in
``infer_from_database``. Only ``steam_games`` is supported here; quotes still
live in Qdrant.

Env:
  S3_VECTORS_BUCKET   required
  S3_VECTORS_INDEX    default: steam_games
  AWS_REGION          default: us-east-1
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import boto3
from fastembed import TextEmbedding
from pathlib import Path

MODEL = "BAAI/bge-small-en-v1.5"
DIM = 384
TOP_K = 10

BUCKET = os.environ.get("S3_VECTORS_BUCKET", "")
INDEX = os.environ.get("S3_VECTORS_INDEX", "steam-games")
REGION = os.environ.get("AWS_REGION", "us-east-1")
_DEFAULT_GENRES = Path(__file__).resolve().parent.parent / "data_raw" / "steam_games.json"
GENRES_SOURCE = os.environ.get("S3_VECTORS_GENRES_SOURCE", str(_DEFAULT_GENRES))


@dataclass
class ScoredPoint:
    """Quacks like ``qdrant_client.models.ScoredPoint`` for the callers in
    ``app_page_steam.py``."""

    id: str
    score: float
    payload: dict


@lru_cache(maxsize=1)
def _client():
    return boto3.client("s3vectors", region_name=REGION)


@lru_cache(maxsize=1)
def _embedder() -> TextEmbedding:
    return TextEmbedding(model_name=MODEL)


@lru_cache(maxsize=1)
def _genres() -> list[str]:
    """S3 Vectors has no facet API; derive the genre set from the source JSON
    once and cache it."""
    try:
        with open(GENRES_SOURCE, "r") as f:
            rows = json.load(f)
    except FileNotFoundError:
        return []
    seen: set[str] = set()
    for row in rows:
        for genre in row.get("genres") or []:
            seen.add(genre)
    return sorted(seen)


def get_unique_types(collection_name: str) -> list[str]:
    if collection_name != "steam_games":
        raise ValueError(f"S3 Vectors backend only handles steam_games, got {collection_name}")
    return list(_genres())


def _embed_query(text: str) -> list[float]:
    vec = next(iter(_embedder().embed([text])))
    return vec.tolist()


def _random_vector() -> list[float]:
    return [random.uniform(-1.0, 1.0) for _ in range(DIM)]


def get_result(
    user_query: str | None,
    collection_name: str,
    domain: str | None = None,
) -> list[ScoredPoint] | None:
    if collection_name != "steam_games":
        raise ValueError(f"S3 Vectors backend only handles steam_games, got {collection_name}")
    if not BUCKET:
        raise RuntimeError("S3_VECTORS_BUCKET env var is required")

    if domain in _genres():
        filt: dict[str, Any] | None = {"genres": {"$in": [domain]}}
    else:
        filt = None

    qvec = _random_vector() if user_query is None else _embed_query(user_query)

    kwargs: dict[str, Any] = {
        "vectorBucketName": BUCKET,
        "indexName": INDEX,
        "queryVector": {"float32": qvec},
        "topK": TOP_K,
        "returnMetadata": True,
        "returnDistance": True,
    }
    if filt is not None:
        kwargs["filter"] = filt

    resp = _client().query_vectors(**kwargs)
    hits = resp.get("vectors") or []
    if not hits:
        return None

    results: list[ScoredPoint] = []
    for hit in hits:
        # S3 Vectors returns "distance" for cosine, in [0, 2]. Convert to a
        # similarity in [0, 1] so the UI's "%fit" reads sensibly.
        distance = hit.get("distance")
        score = 1.0 - (float(distance) / 2.0) if distance is not None else 0.0
        results.append(
            ScoredPoint(
                id=hit.get("key", ""),
                score=score,
                payload=hit.get("metadata") or {},
            )
        )
    return results
