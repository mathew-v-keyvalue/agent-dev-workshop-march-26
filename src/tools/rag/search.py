"""RAG tools: semantic search, hybrid search, and get document by ID over the vector DB."""

from typing import Any

from langchain_core.tools import tool


def create_rag_tools(vector_db: Any) -> list:
    """
    Create LangChain tools for RAG using the given vector database.

    The vector_db must support semantic_search, hybrid_search, and get_documents
    (e.g. WeaviateVectorDB with an embedding instance).

    Returns:
        List of tools: semantic_search, hybrid_search, get_document_by_id.
    """
    db = vector_db

    @tool
    def semantic_search(query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search the policy and help documents by meaning (semantic/vector search).

        Use this for questions about shipping, delivery, returns, cancellation policy,
        refunds, or other company policies. Pass the customer's question or keywords.
        Returns relevant document chunks with content and metadata (e.g. source file).

        Args:
            query: Natural language question or search phrase (e.g. 'What is the return window?').
            top_k: Maximum number of results to return (default 5).
        """
        return db.semantic_search(query, top_k=top_k)

    @tool
    def hybrid_search(
        query: str, top_k: int = 5, alpha: float = 0.5
    ) -> list[dict[str, Any]]:
        """Search policy and help documents with both keyword and semantic relevance (hybrid).

        Use for policy questions when you want both exact keyword match and meaning.
        alpha=1.0 is purely semantic, alpha=0.0 is purely keyword; 0.5 balances both.

        Args:
            query: Search question or phrase.
            top_k: Maximum number of results (default 5).
            alpha: Weight of semantic vs keyword (default 0.5).
        """
        return db.hybrid_search(query, top_k=top_k, alpha=alpha)

    @tool
    def get_document_by_id(doc_id: str) -> dict[str, Any]:
        """Fetch a single document chunk by its ID (e.g. from a prior search result).

        Use when you need the full content of a specific chunk returned by semantic_search
        or hybrid_search.

        Args:
            doc_id: The document chunk ID (UUID string).
        """
        docs = db.get_documents(ids=[doc_id])
        if not docs:
            return {"error": f"No document found with id '{doc_id}'."}
        return docs[0]

    return [semantic_search, hybrid_search, get_document_by_id]
