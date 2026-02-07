from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import ingestion_router, conversation_router
from app.database.redis_client import init_redis, close_redis
from app.database.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")

    # Initialize SQL database (create tables)
    print("🔄 Initializing database...")
    init_db()
    print("✅ Database initialized")

    # Initialize Redis
    await init_redis()
    print("✅ Redis Connected")

    yield

    print("🛑 Shutting down....")
    await close_redis()


app = FastAPI(
    title="RAG Api",
    version="1.0.0",
    description="APIs for Conversational, Document Ingestiontion and Processing",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.include_router(ingestion_router)
app.include_router(conversation_router)
