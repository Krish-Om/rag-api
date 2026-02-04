from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from Document import Document


class ChunkingStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"
    semantic = "semantic"


class Chunk(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    doc_id: int = Field(foreign_key="document.id")
    vector_id: str
    content: str
    chunk_position: int
    chunk_length: int

    document: Document = Relationship(back_populates="chunks")
