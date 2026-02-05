import os

load_dotenv()


class Config:
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:password@localhost:5432/document_db"
        )
        self.redis_url = os.getenv("REDIS_URL", "http://localhost:6379")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")


config = Config()
