from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="RAG Api",
    version="1.0.0",
    description="APIs for Conversational, Document Ingestiontion and Processing",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
# app.include_router(ingestion_router)
