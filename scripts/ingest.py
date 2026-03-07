"""
Ingest documents from the data/ folder into Weaviate for RAG.

Reads .txt and .md files, chunks by character length with overlap,
embeds with OpenAI, and adds to the Documents collection.

Run from repo root:
  uv run python -m scripts.ingest
  # or with options:
  uv run python -m scripts.ingest --data-dir data --chunk-size 1000 --overlap 200
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Project root (parent of scripts/)
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.config import settings
from src.embedding import OpenAIEmbedding
from src.vector_db import WeaviateVectorDB


SUPPORTED_EXTENSIONS = {".txt", ".md"}
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 200


def chunk_by_characters(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """
    Split text into chunks by character length with overlap.

    Each chunk has length at most chunk_size. Consecutive chunks overlap
    by `overlap` characters (step = chunk_size - overlap).

    Args:
        text: Full document text.
        chunk_size: Maximum characters per chunk.
        overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        List of chunk strings.
    """
    if overlap >= chunk_size:
        overlap = max(0, chunk_size - 1)
    step = chunk_size - overlap
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += step
        if end >= len(text):
            break
    return chunks


def load_documents(data_dir: Path) -> list[tuple[str, str]]:
    """
    Load all supported files from data_dir.

    Returns:
        List of (content, source_path) tuples. source_path is the file path
        as string for metadata (e.g. "data/shipping_and_delivery.md").
    """
    data_dir = data_dir.resolve()
    if not data_dir.is_dir():
        return []
    out = []
    for path in sorted(data_dir.iterdir()):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  Warning: could not read {path}: {e}", file=sys.stderr)
            continue
        # Use path relative to repo root for source
        try:
            rel = path.relative_to(_REPO_ROOT)
        except ValueError:
            rel = path
        source = str(rel).replace("\\", "/")
        out.append((content, source))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest documents from data/ into Weaviate (character chunking + overlap)."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=_REPO_ROOT / "data",
        help="Directory containing .txt and .md files (default: data)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Character length per chunk (default: {DEFAULT_CHUNK_SIZE})",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=DEFAULT_OVERLAP,
        help=f"Overlap in characters between consecutive chunks (default: {DEFAULT_OVERLAP})",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the Documents collection before ingesting",
    )
    args = parser.parse_args()

    data_dir = args.data_dir if args.data_dir.is_absolute() else _REPO_ROOT / args.data_dir
    docs = load_documents(data_dir)
    if not docs:
        print("No documents found in", data_dir, file=sys.stderr)
        return 1

    # Chunk all documents
    all_chunks = []
    all_metadatas = []
    for content, source in docs:
        chunks = chunk_by_characters(content, args.chunk_size, args.overlap)
        for chunk in chunks:
            all_chunks.append(chunk)
            all_metadatas.append({"source": source})

    print(f"Loaded {len(docs)} file(s), {len(all_chunks)} chunk(s).")

    embedding = OpenAIEmbedding()
    db = WeaviateVectorDB(
        url=settings.WEAVIATE_URL,
        grpc_port=settings.WEAVIATE_GRPC_PORT,
        embedding=embedding,
    )

    try:
        if args.recreate:
            db.delete_collection("Documents")
            print("Recreated Documents collection.")
        db.create_collection("Documents")
        ids = db.add_documents(all_chunks, metadatas=all_metadatas)
        print(f"Ingested {len(ids)} chunk(s) into Weaviate.")
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
