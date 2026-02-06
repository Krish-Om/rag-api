from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .Document import Document


class Chunk(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    doc_id: int = Field(foreign_key="document.id")
    vector_id: str
    content: str
    chunk_position: int
    chunk_length: int

    document: "Document" = Relationship(back_populates="chunks")
