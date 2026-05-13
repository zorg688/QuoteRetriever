"""Upload steam_games.json into an AWS S3 Vectors index.

Run from src/:  python upload_s3_vectors.py

Required env:
  S3_VECTORS_BUCKET  - name of the vector bucket (must exist)
  AWS_REGION         - region of the bucket (default us-east-1)
  AWS_*              - standard boto3 credential resolution
Optional env:
  S3_VECTORS_INDEX   - index name (default: steam_games)
  S3_VECTORS_DATA    - path to JSON (default: ../data_raw/steam_games.json)
"""

import json
import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from fastembed import TextEmbedding

MODEL = "BAAI/bge-small-en-v1.5"
DIM = 384
BATCH = 500

# Caps so each vector stays under the S3 Vectors per-vector metadata limits
# (filterable <= 2 KB, total <= 40 KB). Limits enforced in bytes (UTF-8).
TOTAL_META_BUDGET = 38_000  # leave headroom under 40 KB cap
DESC_MAX_BYTES = 30_000
SHORT_DESC_MAX_BYTES = 4_000
NAME_MAX_BYTES = 500

FILTERABLE_KEYS = {
    "genres",
    "price",
    "review_score",
    "windows",
    "mac",
    "linux",
    "estimated_owners",
}
NON_FILTERABLE_KEYS = ["name", "short_description", "detailed_description"]


def build_embed_text(row: dict) -> str:
    name = row.get("name", "") or ""
    short = row.get("short_description", "") or ""
    genres = row.get("genres", []) or []
    return f"{name}:{short}:{','.join(genres)}"


def truncate_bytes(s: str, max_bytes: int) -> str:
    encoded = s.encode("utf-8")
    if len(encoded) <= max_bytes:
        return s
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def build_metadata(row: dict) -> dict:
    meta: dict = {}
    for key in FILTERABLE_KEYS:
        val = row.get(key)
        if val is None:
            continue
        if isinstance(val, (list, tuple, str)) and len(val) == 0:
            continue
        meta[key] = val

    name = truncate_bytes(row.get("name") or "", NAME_MAX_BYTES)
    short_desc = truncate_bytes(row.get("short_description") or "", SHORT_DESC_MAX_BYTES)
    detailed = truncate_bytes(row.get("detailed_description") or "", DESC_MAX_BYTES)
    if name:
        meta["name"] = name
    if short_desc:
        meta["short_description"] = short_desc
    if detailed:
        meta["detailed_description"] = detailed

    # Enforce total metadata byte budget by progressively trimming detailed_description.
    while len(json.dumps(meta, ensure_ascii=False).encode("utf-8")) > TOTAL_META_BUDGET:
        if "detailed_description" in meta and len(meta["detailed_description"]) > 1000:
            meta["detailed_description"] = truncate_bytes(
                meta["detailed_description"],
                max(1000, len(meta["detailed_description"].encode("utf-8")) // 2),
            )
        elif "detailed_description" in meta:
            del meta["detailed_description"]
        elif "short_description" in meta:
            del meta["short_description"]
        else:
            break
    return meta


def ensure_index(client, bucket: str, index: str) -> None:
    try:
        client.create_index(
            vectorBucketName=bucket,
            indexName=index,
            dataType="float32",
            dimension=DIM,
            distanceMetric="cosine",
            metadataConfiguration={"nonFilterableMetadataKeys": NON_FILTERABLE_KEYS},
        )
        print(f"Created index {index} in {bucket}")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"ConflictException", "ResourceAlreadyExistsException"}:
            print(f"Index {index} already exists")
        else:
            raise


def flush(client, bucket: str, index: str, batch: list) -> None:
    if not batch:
        return
    client.put_vectors(vectorBucketName=bucket, indexName=index, vectors=batch)


def main() -> int:
    bucket = os.environ.get("S3_VECTORS_BUCKET")
    if not bucket:
        print("S3_VECTORS_BUCKET env var required", file=sys.stderr)
        return 1
    index = os.environ.get("S3_VECTORS_INDEX", "steam-games")
    region = os.environ.get("AWS_REGION", "us-east-1")
    default_data = Path(__file__).resolve().parent.parent / "data_raw" / "steam_games.json"
    data_path = os.environ.get("S3_VECTORS_DATA", str(default_data))

    s3v = boto3.client("s3vectors", region_name=region)
    ensure_index(s3v, bucket, index)

    print(f"Loading {data_path}")
    with open(data_path, "r") as f:
        rows = json.load(f)
    print(f"{len(rows)} rows")

    print(f"Embedding with {MODEL}")
    embedder = TextEmbedding(model_name=MODEL)
    texts = [build_embed_text(r) for r in rows]

    pending: list = []
    total = 0
    for idx, vec in enumerate(embedder.embed(texts, batch_size=64)):
        pending.append(
            {
                "key": str(idx),
                "data": {"float32": vec.tolist()},
                "metadata": build_metadata(rows[idx]),
            }
        )
        if len(pending) >= BATCH:
            flush(s3v, bucket, index, pending)
            total += len(pending)
            print(f"Uploaded {total}/{len(rows)}")
            pending = []

    flush(s3v, bucket, index, pending)
    total += len(pending)
    print(f"Done. Uploaded {total} vectors to {bucket}/{index}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
