# RAG API - Tech Stack Decisions

## Architecture Overview
Building a self-contained, dockerized RAG API system for interview demo and production deployment.

## Core Stack

### Framework
- **FastAPI** - As specified in requirements
- **SQLModel** - For database ORM and API serialization integration

### Databases
- **Metadata Storage**: SQLite (development) / PostgreSQL (production)
- **Vector Storage**: Qdrant (local Docker container)
- **Chat Memory**: Redis (Docker container)

### Embedding & LLM
- **Embedding Model**: `all-MiniLM-L6-v2` (sentence-transformers)
  - 384 dimensions, fast inference, good accuracy
  - Open source, no API keys required
- **LLM**: Ollama with `llama3.2:1b` model
  - Fast responses (~1-2 seconds), low RAM usage
  - Fully local, no API keys required
  - Separate Docker service for clean architecture

### Text Processing
- **PDF Processing**: pdfplumber (better than PyPDF2 for complex layouts)
- **Chunking**: 
  - Fixed-size: Simple character/token-based splitting
  - Semantic: spaCy or sentence-based chunking

## Dependencies to Add
```
sqlmodel>=0.0.32
qdrant-client>=1.0.0
sentence-transformers>=2.0.0
pdfplumber
redis>=4.0.0
spacy>=3.0.0
python-multipart  # For file uploads
python-dotenv     # For environment variables
```

## Deployment Strategy
- **Docker Compose** setup for plug-and-play demo
- Services: FastAPI app, Qdrant, Redis, Ollama
- Single command startup: `docker-compose up`
- Ollama will automatically pull llama3.2:1b model on first run

## Development Approach
- **Synchronous processing** for MVP (mention async as production improvement)
- **Modular architecture** with clear separation of concerns
- **Type hints throughout** for code quality

## Database Schema

### Documents Table
- `id` (Primary Key)
- `file_name`
- `file_path`
- `file_size`
- `doc_type` (PDF/TXT enum)
- `chunking_strat` (fixed_size/semantic enum)
- `upload_date`
- `total_chunk_count`

### Chunks Table
- `id` (Primary Key) 
- `doc_id` (Foreign Key to Documents)
- `vector_id` (Reference to Qdrant vector)
- `content` (Actual text content)
- `chunk_position` (Order in document)
- `chunk_length`

### Bookings Table (for interview booking feature)
- `id` (Primary Key)
- `name`
- `email`
- `date`
- `time`
- `session_id` (link to conversation)
- `created_at`

## API Endpoints

### API 1: Document Ingestion
- `POST /upload` - Upload and process documents
- `GET /documents` - List processed documents
- `GET /documents/{id}` - Get document details

### API 2: Conversational RAG  
- `POST /chat` - Send message and get response (includes booking functionality)
- `GET /chat/sessions` - List chat sessions (optional)
- `POST /chat/sessions` - Create new session (optional)

**Note**: Interview booking is handled within the chat conversation flow, not as separate endpoints. The LLM extracts booking information (name, email, date, time) from natural language and stores it in the database.

## Rationale for Choices
- **Local-first**: No external dependencies for demo
- **Open source**: Cost-effective and customizable
- **Docker**: Professional deployment, easy setup
- **SQLModel**: Type safety and FastAPI integration
- **Qdrant**: Best local vector DB with great docs