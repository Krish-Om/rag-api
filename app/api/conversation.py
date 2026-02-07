from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlmodel import Session
from datetime import datetime
import logging
import uuid

from app.services import (
    LLMService,
    ConversationalRAGService,
    ChatMemoryService,
    BookingParser,
)
from app.services.booking_parser import (
    BookingStatus as ParserBookingStatus,
)  # Renamed to avoid collision
from app.models.Booking import (
    Booking as BookingModel,
    InterviewType,
    BookingStatus as DBBookingStatus,
)
from app.database.db import get_session

logger = logging.getLogger(__name__)

conversation_router = APIRouter(prefix="/api/v1", tags=["Conversational RAG"])

# Initialize services
rag_service = ConversationalRAGService()
llm_service = LLMService()
chat_memory = ChatMemoryService()
booking_parser = BookingParser()


class ChatRequest(BaseModel):
    query: str = Field(..., description="User's query or question")
    session_id: Optional[str] = Field(None, description="Chat session ID")


class BookingResponse(BaseModel):
    booking_detected: bool
    booking_status: str
    extracted_info: Dict[str, Any]
    missing_fields: List[str]
    suggestions: List[str]
    booking_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI-generated response")
    session_id: str = Field(..., description="Chat session ID")
    context_used: bool = Field(..., description="Whether document context was used")
    sources: List[Dict[str, Any]] = Field(
        default=[], description="Source documents used"
    )
    booking_info: Optional[BookingResponse] = Field(
        None, description="Booking information if detected"
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
                "booking": True,
            },
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            services={"llm": False, "redis": False, "rag": False, "booking": False},
        )


@conversation_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_session)):
    """
    Enhanced conversational RAG endpoint with booking detection

    This endpoint:
    1. Generates/validates session ID
    2. Detects and processes booking requests
    3. Retrieves relevant document context using RAG
    4. Generates AI response using LLM with TOON optimization
    5. Stores conversation in Redis for future context
    """

    try:
        session_id = request.session_id or str(uuid.uuid4())

        # Store user message
        await chat_memory.store_message(
            session_id=session_id, role="user", content=request.query
        )

        # Initialize booking_info outside the conditional block
        booking_info = None
        booking_detected = booking_parser.detect_booking_intent(request.query)

        if booking_detected:
            # Process booking with spaCy + LLM
            parsed_booking = await booking_parser.process_booking_with_llm(
                request.query, llm_service
            )

            # Validate booking information
            validation_result = booking_parser.validate_booking_info(parsed_booking)

            booking_response = BookingResponse(
                booking_detected=True,
                booking_status=parsed_booking.status.value,
                extracted_info={
                    "name": parsed_booking.name,
                    "email": parsed_booking.email,
                    "date": parsed_booking.date,
                    "time": parsed_booking.time,
                    "type": parsed_booking.interview_type,
                },
                missing_fields=parsed_booking.missing_fields or [],
                suggestions=validation_result.get("suggestions", []),
            )

            # Store booking if valid and all fields are present
            if (
                parsed_booking.status == ParserBookingStatus.VALID
                and validation_result["is_valid"]
                and parsed_booking.name  # Ensure name not None
                and parsed_booking.email  # Ensure email not None
                and parsed_booking.date  # Ensure date not None
                and parsed_booking.time  # Ensure time not None
                and parsed_booking.interview_type  # Ensure interview_type not None
            ):
                try:
                    # Validate interview type before conversion
                    interview_type_value = parsed_booking.interview_type.lower()
                    if interview_type_value not in [e.value for e in InterviewType]:
                        interview_type_value = "general"  # Fallback to general

                    booking = BookingModel(
                        session_id=session_id,
                        name=parsed_booking.name,  # Now guaranteed not None
                        email=parsed_booking.email,  # Now guaranteed not None
                        booking_date=datetime.strptime(
                            parsed_booking.date, "%Y-%m-%d"  # Now guaranteed not None
                        ).date(),
                        booking_time=datetime.strptime(
                            parsed_booking.time, "%H:%M"  # Now guaranteed not None
                        ).time(),
                        interview_type=InterviewType(
                            interview_type_value
                        ),  # Now safely converted
                        status=DBBookingStatus.PENDING,
                        confidence_score=parsed_booking.confidence,
                        extracted_text=parsed_booking.extracted_text,
                    )

                    db.add(booking)
                    db.commit()
                    db.refresh(booking)

                    booking_response.booking_id = booking.id
                    logger.info(f"Booking successfully created with ID: {booking.id}")

                except ValueError as e:
                    logger.error(f"Data validation error: {e}")
                    db.rollback()
                except Exception as e:
                    logger.error(f"Unexpected error storing booking: {e}")
                    db.rollback()

            # Set booking_info for the response
            booking_info = booking_response

        # Continue with RAG processing
        rag_result = await rag_service.process_query(
            session_id=session_id, query=request.query
        )

        context_chunks = rag_result.get("context_chunks", [])

        # Generate AI response
        ai_response = await llm_service.generate_response(
            query=request.query, context_chunks=context_chunks, session_id=session_id
        )

        # Store AI response
        await chat_memory.store_message(
            session_id=session_id, role="assistant", content=ai_response
        )

        # Prepare sources
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
            booking_info=booking_info,  # Fixed: now always defined
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
        format: Response format ("json" or "toon")
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
