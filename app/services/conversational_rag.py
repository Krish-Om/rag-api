from typing import List,Dict,Any,Optional
from app.services import EmbeddingService,VectorService,ChatMemoryService
import logging

logger = logging.getLogger(__name__)

class ConversationalRAGService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.chat_memory = ChatMemoryService()


    async def process_query(self,session_id:str,query:str) -> Dict[str,Any]:
        """Entry point"""

        try:
            chat_history = await self.chat_memory.get_chat_history_json(session_id=session_id)

            context_chunks = await self._retrieve_context(query)

            return {
                "query":query,
                "context_chunks":context_chunks,
                "chat_history":chat_history,
                "has_context":len(context_chunks)>0
            }
        
        except Exception as e:
            logger.error(f"Error in RAG processing:{e}")
            raise


    async def _retrieve_context(self,query:str) -> List[Dict]:
        """Basic context retrieval"""
        try:
            q_vector = self.embedding_service.generate_single_embeddings(query)

            similar_chunks = self.vector_service.search_similar(
                query_vector=q_vector,
                limit=3
            )

            return similar_chunks
        
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []