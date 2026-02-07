from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import uuid


from app.services import (
    LLMService,
    ConversationalRAGService,
    ChatMemoryService,
)

logger = logging.getLogger(__name__)

conversation_router = APIRouter(prefix="/api/v1", tags=["Conversational RAG"])

rag_service = ConversationalRAGService()
llm_service = LLMService()
chat_memory = ChatMemoryService()


class ChatRequest(BaseModel):
    query: str = Field(..., description="User's query or question")
    session_id: Optional[str] = Field(None, description="Chat session ID")


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI-generate response")
    session_id: str = Field(..., description="Chat session ID")
    context_used: bool = Field(..., description="Whether document context was used")
    sources: List[Dict[str, Any]] = Field(
        default=[], description="Source documents used"
    )


class HealthResponse(BaseModel):
    status: str
    services: Dict[str, bool]


@conversation_router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check health of all conversation services"""
    try:
        llm_health = await llm_service.health_check()

        try:
            await chat_memory.get_chat_history_json("health_check")
            redis_health = True
        except:
            redis_health = False

        return HealthResponse(
            status="healthy" if llm_health and redis_health else "degraded",
            services={
                "llm": llm_health,
                "redis": redis_health,
                "rag": True,
            },
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy", services={"llm": False, "redis": False, "rag": False}
        )


@conversation_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main conversational RAG endpoint

    This endpoint:
    1. Generates/validates session ID
    2. Retreives relevant document context using RAG
    3. Generate AI response using LLM with TOON optimization
    4. Stores conversation in Redis for future context
    """

    try:
        session_id = request.session_id or str(uuid.uuid4())

        await chat_memory.store_message(
            session_id=session_id, role="user", content=request.query
        )

        rag_result = await rag_service.process_query(
            session_id=session_id, query=request.query
        )

        context_chunks = rag_result.get("context_chunks", [])

        ai_response = await llm_service.generate_response(
            query=request.query, context_chunks=context_chunks, session_id=session_id
        )

        await chat_memory.store_message(
            session_id=session_id, role="assistant", content=ai_response
        )

        sources = [
            {
                "doc_id": chunk.get("doc_id", "unknown"),
                "content_preview": chunk.get("content", "")[:100] + "...",
                "score": chunk.get("score", 0.0),
            }
            for chunk in context_chunks[:3]
        ]

        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            context_used=len(context_chunks) > 0,
            sources=sources,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}",
        )


@conversation_router.get("/chat/{session_id}/history")
async def get_chat_history(session_id: str, format: str = "json"):
    """
    Retrieve chat history for a session.

    Args:
        session_id: The chat session ID
        format: Response format("json" or "toon")
    """

    try:
        if format.lower() == "toon":
            history = await chat_memory.get_chat_history_toon(session_id)
            return {"session_id": session_id, "format": "toon", "history": history}
        else:
            history = await chat_memory.get_chat_history_json(session_id)
            return {"session_id": session_id, "format": "json", "history": history}

    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chat history: {str(e)}",
        )
