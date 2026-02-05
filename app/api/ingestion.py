from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
import logging

from app.services import (
    TextExtractionService,
    VectorService,
    EmbeddingService,
    ChunkingService,
)
from app.models import Document, Chunk, DocumentType, ChunkingStrategy
from app.database.db import get_session

logger = logging.getLogger(__name__)

ingestion_router = APIRouter(prefix="/api/v1", tags=["Document Ingestion"])
text_extraction_service = TextExtractionService()
vector_service = VectorService()
embedding_service = EmbeddingService()
chunking_service = ChunkingService()


@ingestion_router.post("/upload")
async def upload_document(
    uploaded_file: UploadFile = File(...),
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,  # Default to semantic
    session: Session = Depends(get_session),
):
    """
    Upload and process a document (PDF or TXT)

    :param file: pdf or txt \n
    :type file: UploadFile \n
    :param chunking_strategy: fixed_size or semantic \n
    :type chunking_strategy: ChunkingStrategy \n
    :param session: postgres database session \n
    :type session: Session

    """

    try:
        if not uploaded_file:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail=f"No file content attached",
            )

        extracted_text = await text_extraction_service.extract_text_from_file(
            file=uploaded_file
        )
        logger.info(f"Text extracted successfully: {len(extracted_text)} characters")

        chunk_result = chunking_service.chunk_text(
            extracted_text, strategy=chunking_strategy
        )
        logger.info(
            f"Document chunked: {chunk_result.total_chunks} chunks using {chunking_strategy.value}"
        )

        embeddings = embedding_service.generate_embeddings(chunk_result.chunks)
        logger.info(f"Generated {len(embeddings)} embeddings")

        filename = uploaded_file.filename or "unknown"
        metadata = Document(
            file_name=filename,
            file_path=filename,
            file_size=uploaded_file.size or 0,
            doc_type=(
                DocumentType.PDF if filename.endswith(".pdf") else DocumentType.TXT
            ),
            chunking_strat=chunking_strategy,
            total_chunk_count=chunk_result.total_chunks,
        )
        # 1. Save Document metadata to SQL db and get ID
        session.add(metadata)
        session.commit()
        session.refresh(metadata)
        doc_id = metadata.id or 0
        logger.info(f"Document metadata saved with ID: {doc_id}")

        # 2 Store embeddings in vector db and get vector id
        vector_ids = vector_service.store_vectors(
            vectors=embeddings,
            chunk_ids=[],
            doc_id=doc_id,
            contents=chunk_result.chunks,
        )
        logger.info(f"Stored {len(vector_ids)} vectors in Qdrant")

        chunk_records = []
        for i, (chunk_text, chunk_length, vector_id) in enumerate(
            zip(chunk_result.chunks, chunk_result.chunk_lengths, vector_ids)
        ):
            chunk_record = Chunk(
                doc_id=doc_id,
                vector_id=vector_id,
                content=chunk_text,
                chunk_position=i,
                chunk_length=chunk_length,
            )
            chunk_records.append(chunk_record)
            session.add(chunk_record)
        logger.info(f"Created {len(chunk_records)} chunk records in database")

        session.commit()
        logger.info(
            f"Document processing completed successfully: {filename} (ID: {doc_id})"
        )
        return {"message": f"Document successfully uploaded"}
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document :{str(e)}",
        )
