"""
Weaviate vector database implementation.

Connects to a Weaviate instance (e.g. Docker on HTTP 8090 / gRPC 50051)
with self-provided vectors (no vectorizer). Requires an embedding instance
for add_documents, semantic_search, and hybrid_search.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Protocol
import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.data import DataObject
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.connect.base import ConnectionParams

from src.vector_db.base import VectorDBBase


class EmbeddingProtocol(Protocol):
    """Protocol for embedding provider (e.g. OpenAIEmbedding)."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


# Default collection name used by RAG (ingest, run_checkpoint_evals)
DEFAULT_COLLECTION_NAME = "Documents"

# Standard property for document text
CONTENT_PROP = "content"
SOURCE_PROP = "source"
# Extra metadata stored as JSON for filter/retrieval
META_JSON_PROP = "metadata_json"


def _build_where(metadata_filter: dict[str, Any] | None) -> Filter | None:
    """Build Weaviate Filter from a flat metadata dict (AND of equal conditions)."""
    if not metadata_filter:
        return None
    filters = [
        Filter.by_property(k).equal(v) for k, v in metadata_filter.items()
    ]
    if not filters:
        return None
    out = filters[0]
    for f in filters[1:]:
        out = out & f
    return out


def _props_from_meta(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Convert metadata dict to Weaviate properties (content not included)."""
    if not metadata:
        return {}
    props = {}
    if "source" in metadata:
        props[SOURCE_PROP] = str(metadata["source"])
    rest = {k: v for k, v in metadata.items() if k != "source"}
    if rest:
        props[META_JSON_PROP] = json.dumps(rest)
    return props


def _meta_from_props(properties: dict[str, Any]) -> dict[str, Any]:
    """Build metadata dict from Weaviate properties."""
    meta = {}
    if SOURCE_PROP in properties:
        meta["source"] = properties[SOURCE_PROP]
    if META_JSON_PROP in properties and properties[META_JSON_PROP]:
        try:
            meta.update(json.loads(properties[META_JSON_PROP]))
        except (json.JSONDecodeError, TypeError):
            pass
    return meta


class WeaviateVectorDB(VectorDBBase):
    """
    Weaviate implementation of VectorDBBase.

    Uses HTTP + gRPC to the Weaviate server (e.g. http://localhost:8090, gRPC 50051).
    Vectors are self-provided; pass an embedding instance for indexing and search.
    """

    def __init__(
        self,
        url: str = "http://localhost:8090",
        grpc_port: int = 50051,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        embedding: EmbeddingProtocol | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Weaviate client.

        Args:
            url: Weaviate HTTP URL (e.g. http://localhost:8090 or http://weaviate:8080 in Docker).
            grpc_port: gRPC port (default 50051).
            collection_name: Class/collection name (default "Documents").
            embedding: Optional embedding for add_documents and semantic/hybrid search.
            **kwargs: Ignored (for base compatibility).
        """
        self._url = url
        self._grpc_port = grpc_port
        self._collection_name = collection_name
        self._embedding = embedding
        self._client = weaviate.WeaviateClient(
            connection_params=ConnectionParams.from_url(
                url=url, grpc_port=grpc_port
            )
        )
        self._client.connect()

    def _collection(self):
        return self._client.collections.get(self._collection_name)

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        if self._embedding is None:
            raise ValueError(
                "WeaviateVectorDB requires an embedding instance for add_documents"
            )
        vectors = self._embedding.embed_documents(documents)
        metadatas = metadatas or [{}] * len(documents)
        if len(metadatas) != len(documents):
            metadatas = (metadatas + [{}] * len(documents))[: len(documents)]
        objects = []
        for i, (doc, vec) in enumerate(zip(documents, vectors)):
            meta = metadatas[i] if i < len(metadatas) else {}
            props = {CONTENT_PROP: doc, **_props_from_meta(meta)}
            obj_id = None
            if ids and i < len(ids):
                try:
                    obj_id = uuid.UUID(ids[i])
                except (ValueError, TypeError):
                    pass
            obj = DataObject(properties=props, vector=vec, uuid=obj_id)
            objects.append(obj)
        result = self._collection().data.insert_many(objects)
        return [str(result.uuids[i]) for i in sorted(result.uuids.keys())]

    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        if self._embedding is None:
            raise ValueError(
                "WeaviateVectorDB requires an embedding instance for semantic_search"
            )
        query_vector = self._embedding.embed_query(query)
        coll = self._collection()
        where = _build_where(metadata_filter)
        res = coll.query.near_vector(
            near_vector=query_vector,
            limit=top_k,
            return_metadata=MetadataQuery(distance=True),
            filters=where,
        )
        return _results_to_list(res)

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
        metadata_filter: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        if self._embedding is None:
            raise ValueError(
                "WeaviateVectorDB requires an embedding instance for hybrid_search"
            )
        query_vector = self._embedding.embed_query(query)
        coll = self._collection()
        where = _build_where(metadata_filter)
        res = coll.query.hybrid(
            query=query,
            vector=query_vector,
            limit=top_k,
            alpha=alpha,
            return_metadata=MetadataQuery(score=True),
            filters=where,
        )
        return _results_to_list(res)

    def delete_documents(
        self,
        ids: list[str] | None = None,
        metadata_filter: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> bool:
        coll = self._collection()
        if ids:
            for doc_id in ids:
                try:
                    coll.data.delete_by_id(uuid.UUID(doc_id))
                except (ValueError, TypeError):
                    pass
            return True
        where = _build_where(metadata_filter)
        if where is None:
            return False
        coll.data.delete_many(where=where)
        return True

    def update_documents(
        self,
        ids: list[str],
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> bool:
        if self._embedding is None and documents:
            raise ValueError(
                "WeaviateVectorDB requires an embedding instance to update document content"
            )
        coll = self._collection()
        vectors = (
            self._embedding.embed_documents(documents)
            if documents and self._embedding
            else [None] * len(ids)
        )
        if documents and len(vectors) != len(ids):
            vectors = (vectors + [None] * len(ids))[: len(ids)]
        metadatas = metadatas or [{}] * len(ids)
        if len(metadatas) != len(ids):
            metadatas = (metadatas + [{}] * len(ids))[: len(ids)]
        for i, doc_id in enumerate(ids):
            try:
                uid = uuid.UUID(doc_id)
            except (ValueError, TypeError):
                continue
            props = None
            if documents and i < len(documents):
                meta = metadatas[i] if i < len(metadatas) else {}
                props = {CONTENT_PROP: documents[i], **_props_from_meta(meta)}
            elif metadatas and i < len(metadatas):
                props = _props_from_meta(metadatas[i])
            vec = vectors[i] if i < len(vectors) else None
            if props is not None or vec is not None:
                coll.data.replace(uuid=uid, properties=props, vector=vec)
        return True

    def get_documents(
        self,
        ids: list[str] | None = None,
        metadata_filter: dict[str, Any] | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        coll = self._collection()
        if ids:
            out = []
            for doc_id in ids:
                try:
                    obj = coll.query.fetch_object_by_id(uuid.UUID(doc_id))
                    if obj is not None:
                        out.append(_object_to_result(obj))
                except (ValueError, TypeError):
                    pass
            return out
        where = _build_where(metadata_filter)
        res = coll.query.fetch_objects(
            filters=where, limit=limit or 100
        )
        return [_object_to_result(o) for o in res.objects]

    def create_collection(self, collection_name: str, **kwargs: Any) -> bool:
        name = collection_name or self._collection_name
        if self._client.collections.exists(name):
            return True
        self._client.collections.create(
            name,
            vector_config=Configure.Vectors.self_provided(),
            properties=[
                Property(name=CONTENT_PROP, data_type=DataType.TEXT),
                Property(name=SOURCE_PROP, data_type=DataType.TEXT),
                Property(name=META_JSON_PROP, data_type=DataType.TEXT),
            ],
        )
        return True

    def delete_collection(self, collection_name: str, **kwargs: Any) -> bool:
        name = collection_name or self._collection_name
        if not self._client.collections.exists(name):
            return True
        self._client.collections.delete(name)
        return True

    def list_collections(self, **kwargs: Any) -> list[str]:
        return list(self._client.collections.list_all())

    def close(self) -> None:
        self._client.close()


def _object_to_result(obj: Any) -> dict[str, Any]:
    p = obj.properties or {}
    content = p.get(CONTENT_PROP, "")
    meta = _meta_from_props(p)
    return {"content": content, "metadata": meta, "id": str(obj.uuid)}


def _results_to_list(res: Any) -> list[dict[str, Any]]:
    out = []
    for obj in res.objects:
        entry = _object_to_result(obj)
        if hasattr(obj, "metadata") and obj.metadata is not None:
            if getattr(obj.metadata, "distance", None) is not None:
                entry["score"] = float(obj.metadata.distance)
            elif getattr(obj.metadata, "score", None) is not None:
                entry["score"] = float(obj.metadata.score)
        out.append(entry)
    return out
