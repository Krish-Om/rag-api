import os
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Filter,
    PointStruct,
    VectorParams,
    FieldCondition,
    MatchValue,
)
from qdrant_client.http.exceptions import UnexpectedResponse
import logging

from app.config import config

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(self):
        self.client = QdrantClient(url=config.qdrant_url)
        self.collection_name = "document_chunks"
        self.vector_size = 384  # all-MiniLM-L6-v2 dimensions
        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=Distance.COSINE
                    ),
                )
                logger.info(f"Collection {self.collection_name} created successfully")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise

    def store_vectors(
        self,
        vectors: List[List[float]],
        chunk_ids: List[int],
        doc_id: int,
        contents: List[str],
    ) -> List[str]:
        """
        Store vectors in Qdrant with metadata linking to SQL database

        Args:
            vectors: List of embedding vectors
            chunk_ids: List of chunk IDs from SQL database
            doc_id: Document ID from SQL database
            contents: List of text contents for each chunk

        Returns:
            List of vector IDs in Qdrant
        """
        try:
            points = []
            vector_ids = []

            for i, (vector, chunk_id, content) in enumerate(
                zip(vectors, chunk_ids, contents)
            ):
                vector_id = str(uuid.uuid4())
                vector_ids.append(vector_id)

                point = PointStruct(
                    id=vector_id,
                    vector=vector,
                    payload={
                        "chunk_id": chunk_id,
                        "doc_id": doc_id,
                        "content": content[:1000],  # Limit content size for storage
                        "chunk_position": i,
                    },
                )
                points.append(point)

            # Batch upload to Qdrant
            self.client.upsert(collection_name=self.collection_name, points=points)

            logger.info(f"Stored {len(points)} vectors for document {doc_id}")
            return vector_ids

        except Exception as e:
            logger.error(f"Error storing vectors: {e}")
            raise

    def search_similar(
        self, query_vector: List[float], limit: int = 5, doc_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            doc_id: Optional filter by document ID

        Returns:
            List of similar chunks with scores and metadata
        """
        try:
            search_filter = None
            if doc_id:
                search_filter = Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                )

            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                with_payload=True,
            )

            results = []
            for result in search_result:
                results.append(
                    {
                        "chunk_id": result.payload["chunk_id"],
                        "doc_id": result.payload["doc_id"],
                        "content": result.payload["content"],
                        "score": result.score,
                        "vector_id": result.id,
                    }
                )

            logger.info(f"Found {len(results)} similar chunks")
            return results

        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise

    def delete_document_vectors(self, doc_id: int) -> bool:
        """
        Delete all vectors for a specific document

        Args:
            doc_id: Document ID to delete vectors for

        Returns:
            Success status
        """
        try:
            delete_filter = Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            )

            self.client.delete(
                collection_name=self.collection_name, points_selector=delete_filter
            )

            logger.info(f"Deleted vectors for document {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document vectors: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the vector collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "vectors_count": info.vectors_count,
                "vector_size": self.vector_size,
                "distance": "COSINE",
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}

    def health_check(self) -> bool:
        """Check if Qdrant service is healthy"""
        try:
            collections = self.client.get_collections()
            if collections:
                return True
            else:
                raise Exception("Qdrant is not healthy")
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


