import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        # Qdrant URL: support both QDRANT_URL or build from QDRANT_HOST+QDRANT_PORT
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = os.getenv("QDRANT_PORT", "6333")
        self.qdrant_url = os.getenv("QDRANT_URL", f"http://{qdrant_host}:{qdrant_port}")

        self.db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:password@localhost:5432/document_db"
        )
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")


config = Config()
