import os
from typing import Any, Dict, List, Optional
import chromadb
from sentence_transformers import SentenceTransformer


class MOVectorEngine:
    """
    Vector engine for Modus Operandi (MO) crime narratives using ChromaDB and Sentence Transformers.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        model_name: str = "all-MiniLM-L6-v2",
        collection_name: str = "modus_operandi",
    ):
        """
        Initialize ChromaDB PersistentClient, load embedding model, and get/create collection.

        Args:
            persist_directory: Filesystem path to persist ChromaDB data.
            model_name: SentenceTransformer model name/path.
            collection_name: Name of the ChromaDB collection.
        """
        if persist_directory is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            persist_directory = os.path.join(base_dir, "chroma_db")

        os.makedirs(persist_directory, exist_ok=True)
        self.persist_directory = persist_directory

        # Initialize ChromaDB Persistent Client
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # Load SentenceTransformer model
        self.model = SentenceTransformer(model_name)

        # Get or create Modus Operandi collection with cosine similarity
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _sanitize_metadata(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ensure metadata fields adhere to ChromaDB specifications (str, int, float, bool).
        """
        if not metadata:
            return {}

        sanitized: Dict[str, Any] = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                sanitized[str(key)] = value
            else:
                sanitized[str(key)] = str(value)
        return sanitized

    def add_case_narrative(
        self,
        case_id: Any,
        narrative_text: str,
        metadata_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Generate dense embeddings for narrative_text and upsert them into the ChromaDB collection.

        Args:
            case_id: Unique identifier for the case.
            narrative_text: Full narrative description of the case or modus operandi.
            metadata_dict: Optional dictionary of associated metadata attributes.
        """
        if not narrative_text or not str(narrative_text).strip():
            raise ValueError("narrative_text cannot be empty.")

        # Generate dense embedding
        embedding = self.model.encode(str(narrative_text))
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()

        # Sanitize metadata for ChromaDB compatibility
        sanitized_metadata = self._sanitize_metadata(metadata_dict)

        # Upsert record into ChromaDB
        self.collection.upsert(
            ids=[str(case_id)],
            embeddings=[embedding],
            documents=[str(narrative_text)],
            metadatas=[sanitized_metadata],
        )

    def search_similar_cases(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for cases with similar modus operandi using dense embeddings.

        Args:
            query_text: Narrative text or search query to match against.
            top_k: Maximum number of similar cases to return (default: 5).

        Returns:
            List of dictionaries containing matched case IDs, narratives,
            similarity scores, and metadata.
        """
        if not query_text or not str(query_text).strip():
            return []

        count = self.collection.count()
        if count == 0:
            return []

        # Clamp top_k to available document count
        n_results = max(1, min(int(top_k), count))

        query_embedding = self.model.encode(str(query_text))
        if hasattr(query_embedding, "tolist"):
            query_embedding = query_embedding.tolist()

        query_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        matched_cases: List[Dict[str, Any]] = []
        if query_results and "ids" in query_results and query_results["ids"]:
            ids = query_results["ids"][0]
            documents = query_results.get("documents", [[]])[0] if query_results.get("documents") else []
            metadatas = query_results.get("metadatas", [[]])[0] if query_results.get("metadatas") else []
            distances = query_results.get("distances", [[]])[0] if query_results.get("distances") else []

            for i, case_id in enumerate(ids):
                narrative = documents[i] if i < len(documents) else ""
                meta = metadatas[i] if i < len(metadatas) and metadatas[i] is not None else {}
                dist = distances[i] if i < len(distances) and distances[i] is not None else 0.0
                similarity = max(0.0, min(1.0, round(1.0 - float(dist), 4)))

                matched_cases.append({
                    "case_id": case_id,
                    "narrative": narrative,
                    "similarity_score": similarity,
                    "metadata": meta,
                })

        return matched_cases

    def query_similar_cases(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve cases with similar modus operandi by querying dense embeddings.

        Args:
            query_text: Search query or suspect narrative.
            n_results: Top N matching cases to retrieve.
            where: Optional metadata filter dict for ChromaDB.

        Returns:
            Dictionary with matching IDs, documents, metadatas, and distances.
        """
        query_embedding = self.model.encode(str(query_text))
        if hasattr(query_embedding, "tolist"):
            query_embedding = query_embedding.tolist()

        query_params: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
        }
        if where:
            query_params["where"] = where

        return self.collection.query(**query_params)

    def get_case(self, case_id: Any) -> Dict[str, Any]:
        """
        Fetch a specific case record by case_id.
        """
        return self.collection.get(ids=[str(case_id)])

    def delete_case(self, case_id: Any) -> None:
        """
        Delete a specific case record by case_id.
        """
        self.collection.delete(ids=[str(case_id)])

    def count(self) -> int:
        """
        Return the total number of case narratives in the collection.
        """
        return self.collection.count()


if __name__ == "__main__":
    # Quick sanity demonstration
    engine = MOVectorEngine()
    print(f"MOVectorEngine initialized. Current collection size: {engine.count()}")
