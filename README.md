# RAG API - Conversational Document Processing System

A comprehensive **FastAPI-based backend** for document ingestion and conversational retrieval-augmented generation (RAG) with intelligent interview booking capabilities.

## 🚀 Overview

This system implements two main APIs:
- **API 1: Document Ingestion** - Upload, process, and vectorize documents
- **API 2: Conversational RAG** - Chat with documents + AI-powered interview booking

### ✨ Key Features

- **Document Processing**: PDF/TXT upload with intelligent chunking strategies
- **Vector Search**: Qdrant-powered similarity search with 384D ONNX-optimized embeddings  
- **Conversational Memory**: Redis-based chat sessions with TOON optimization
- **Smart Booking**: spaCy + LLM hybrid for extracting interview details
- **Multi-Database**: PostgreSQL + Qdrant + Redis architecture
- **Type-Safe**: Full TypeScript-style typing throughout Python codebase
- **Performance Optimized**: ONNX Runtime for fast embedding generation

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        API["`📡 **REST API Clients**
        - Document Upload
        - Chat Requests
        - Booking Management`"]
    end
    
    subgraph "FastAPI Application"
        APP["`🚀 **FastAPI App**
        - Request Routing
        - Authentication
        - Error Handling`"]
        
        subgraph "API Layer"
            DOC_API["`📄 **Document API**
            /api/v1/upload`"]
            CONV_API["`💬 **Conversation API**
            /api/v1/chat`"]
            HEALTH["`❤️ **Health Check**
            /api/v1/health`"]
        end
        
        subgraph "Service Layer"
            TEXT_SVC["`📝 **Text Extraction**
            PDF/TXT Processing`"]
            CHUNK_SVC["`✂️ **Chunking Service**
            Fixed-size & Semantic`"]
            EMBED_SVC["`🧠 **Embedding Service**
            ONNX Runtime + Transformers`"]
            VECTOR_SVC["`🔍 **Vector Service**
            Qdrant Operations`"]
            RAG_SVC["`🤖 **RAG Service**
            Custom Retrieval`"]
            CHAT_SVC["`💭 **Chat Memory**
            TOON Optimization`"]
            BOOK_SVC["`📅 **Booking Parser**
            spaCy + LLM Hybrid`"]
            LLM_SVC["`🧙 **LLM Service**
            Ollama Integration`"]
        end
    end
    
    subgraph "Data Layer"
        PG["`🐘 **PostgreSQL**
        - Documents
        - Chunks  
        - Bookings`"]
        QDRANT["`📊 **Qdrant**
        - Vector Storage
        - Similarity Search
        - 384D Embeddings`"]
        REDIS["`⚡ **Redis**
        - Chat Sessions
        - TOON Format
        - Memory Cache`"]
    end
    
    subgraph "External Services"
        OLLAMA["`🦙 **Ollama**
        - llama3.2:1b
        - Local LLM
        - Booking Enhancement`"]
    end
    
    %% Data Flow
    API --> APP
    APP --> DOC_API
    APP --> CONV_API
    APP --> HEALTH
    
    DOC_API --> TEXT_SVC
    TEXT_SVC --> CHUNK_SVC
    CHUNK_SVC --> EMBED_SVC
    EMBED_SVC --> VECTOR_SVC
    VECTOR_SVC --> QDRANT
    
    DOC_API --> PG
    
    CONV_API --> RAG_SVC
    CONV_API --> CHAT_SVC
    CONV_API --> BOOK_SVC
    
    RAG_SVC --> VECTOR_SVC
    RAG_SVC --> LLM_SVC
    
    CHAT_SVC --> REDIS
    BOOK_SVC --> LLM_SVC
    BOOK_SVC --> PG
    
    LLM_SVC --> OLLAMA
    
    %% Styling
    classDef apiStyle fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef serviceStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef dataStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef externalStyle fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    
    class DOC_API,CONV_API,HEALTH apiStyle
    class TEXT_SVC,CHUNK_SVC,EMBED_SVC,VECTOR_SVC,RAG_SVC,CHAT_SVC,BOOK_SVC,LLM_SVC serviceStyle
    class PG,QDRANT,REDIS dataStyle
    class OLLAMA externalStyle
```

## 📋 Requirements

- **Python**: 3.13+
- **PostgreSQL**: 12+
- **Redis**: 6+
- **Qdrant**: 1.0+
- **Ollama**: For LLM inference (llama3.2:1b model)

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/Krish-Om/rag-api.git
cd rag-api
```

### 2. Install Dependencies
```bash
pip install -e .
```

### 3. Install spaCy Model
```bash
python -m spacy download en_core_web_sm
```

### 4. Setup Environment Variables
Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/document_db

# Vector Database  
QDRANT_URL=http://localhost:6333

# Cache & Memory
REDIS_URL=redis://localhost:6379

# LLM Service
OLLAMA_URL=http://localhost:11434
```

### 5. Start Required Services

**PostgreSQL:**
```bash
# Install and start PostgreSQL
sudo service postgresql start
createdb document_db
```

**Redis:**
```bash
# Install and start Redis
sudo service redis-server start
```

**Qdrant:**
```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant
```

**Ollama:**
```bash
# Install Ollama and pull model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:1b
ollama serve
```

### 6. Run the Application
```bash
uvicorn app.app:app --reload --port 8000
```

## 📚 API Documentation

### Base URL: `http://localhost:8000`

### Authentication
Currently no authentication required. In production, consider implementing:
- API Key authentication
- JWT tokens for session management
- Rate limiting per client

---

## API 1: Document Ingestion

### **POST** `/api/v1/upload`
Upload and process documents (PDF/TXT) with intelligent chunking and vectorization.

#### Request
**Content-Type:** `multipart/form-data`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uploaded_file` | File | ✅ Yes | PDF or TXT file (max 10MB) |
| `chunking_strategy` | string | ❌ No | `"fixed_size"` or `"semantic"` (default: `"semantic"`) |

#### Response
**Success (200):**
```json
{
  "message": "Document successfully uploaded",
  "document_id": 123,
  "filename": "research_paper.pdf",
  "chunks_created": 15,
  "processing_time_ms": 2340
}
```

**Error (400) - Invalid File:**
```json
{
  "detail": "Unsupported file type. Only PDF and TXT files are allowed."
}
```

**Error (413) - File Too Large:**
```json
{
  "detail": "File size exceeds maximum limit of 10MB"
}
```

**Error (500) - Processing Failed:**
```json
{
  "detail": "Error processing document: Unable to extract text from PDF"
}
```

#### Example Usage
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
     -F "uploaded_file=@document.pdf" \
     -F "chunking_strategy=semantic"
```

#### Supported File Types
- **PDF**: All standard PDF formats, including scanned documents
- **TXT**: Plain text files with UTF-8 encoding

#### Chunking Strategies
- **`fixed_size`**: Fixed character chunks (800 chars) with 100 char overlap
- **`semantic`**: Intelligent sentence and paragraph boundary chunking using spaCy

---

## API 2: Conversational RAG

### **POST** `/api/v1/chat`
Main conversational endpoint supporting document queries and booking detection.

#### Request
**Content-Type:** `application/json`

```json
{
  "query": "string (required)",
  "session_id": "string (optional)"
}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ Yes | User's question or booking request (max 1000 chars) |
| `session_id` | string | ❌ No | UUID for session continuity. Auto-generated if not provided |

#### Response Schema
```json
{
  "response": "string",
  "session_id": "string", 
  "context_used": "boolean",
  "sources": [
    {
      "doc_id": "string",
      "content_preview": "string",
      "score": "number"
    }
  ],
  "booking_info": {
    "booking_detected": "boolean",
    "booking_status": "string",
    "extracted_info": {
      "name": "string",
      "email": "string", 
      "date": "string",
      "time": "string",
      "type": "string"
    },
    "missing_fields": ["string"],
    "suggestions": ["string"],
    "booking_id": "number"
  }
}
```

#### Booking Status Values
| Status | Description |
|--------|-------------|
| `"detected"` | Booking intent found but incomplete |
| `"incomplete"` | Missing required fields |
| `"valid"` | All fields present and valid |
| `"invalid"` | Invalid data format |

#### Interview Types
- `"technical"` - Coding/technical assessment
- `"hr"` - HR/behavioral interview  
- `"phone"` - Phone screening
- `"video"` - Video conference
- `"onsite"` - In-person interview
- `"general"` - Default type

#### Example Responses

**Document Query:**
```json
{
  "response": "Machine learning is a subset of artificial intelligence that enables computers to learn patterns from data without explicit programming...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "context_used": true,
  "sources": [
    {
      "doc_id": "123",
      "content_preview": "Machine learning algorithms can be categorized into supervised, unsupervised...",
      "score": 0.89
    }
  ],
  "booking_info": null
}
```

**Booking Request:**
```json
{
  "response": "I'd be happy to help you schedule that interview, John. I have all the information needed and have created your booking.",
  "session_id": "550e8400-e29b-41d4-a716-446655440000", 
  "context_used": false,
  "sources": [],
  "booking_info": {
    "booking_detected": true,
    "booking_status": "valid",
    "extracted_info": {
      "name": "John Smith",
      "email": "john@example.com",
      "date": "2026-02-08", 
      "time": "14:00",
      "type": "technical"
    },
    "missing_fields": [],
    "suggestions": [],
    "booking_id": 456
  }
}
```

**Incomplete Booking:**
```json
{
  "response": "I can help you schedule an interview. I need a few more details to complete your booking.",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "context_used": false,
  "sources": [],
  "booking_info": {
    "booking_detected": true,
    "booking_status": "incomplete", 
    "extracted_info": {
      "name": null,
      "email": null,
      "date": null,
      "time": null,
      "type": "general"
    },
    "missing_fields": ["name", "email", "date", "time"],
    "suggestions": [
      "Please provide your full name",
      "Please provide your email address",
      "Please specify the date (e.g., 2024-02-15 or 'tomorrow')",
      "Please specify the time (e.g., 2:30 PM or 14:30)"
    ],
    "booking_id": null
  }
}
```

#### Error Responses
**400 - Bad Request:**
```json
{
  "detail": "Query cannot be empty"
}
```

**500 - Internal Server Error:**
```json
{
  "detail": "Error processing chat request: LLM service unavailable"
}
```

---

### **GET** `/api/v1/chat/{session_id}/history`
Retrieve conversation history for a specific session.

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | ✅ Yes | Valid session UUID |
| `format` | string | ❌ No | `"json"` or `"toon"` (default: `"json"`) |

#### Response
**JSON Format:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "format": "json",
  "history": [
    {
      "role": "user",
      "content": "What is machine learning?",
      "timestamp": "2026-02-07T14:30:00Z",
      "metadata": {}
    },
    {
      "role": "assistant", 
      "content": "Machine learning is a subset of artificial intelligence...",
      "timestamp": "2026-02-07T14:30:02Z",
      "metadata": {}
    }
  ]
}
```

**TOON Format (Token Optimized):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "format": "toon",
  "history": "history[2]{role,content,timestamp}:\n  user,What is machine learning?,2026-02-07T14:30:00Z\n  assistant,Machine learning is a subset...,2026-02-07T14:30:02Z"
}
```

---

### **GET** `/api/v1/health`
Service health monitoring endpoint.

#### Response
```json
{
  "status": "healthy",
  "services": {
    "llm": true,
    "redis": true, 
    "rag": true,
    "booking": true
  },
  "timestamp": "2026-02-07T14:30:00Z",
  "version": "1.0.0"
}
```

#### Status Values
- `"healthy"` - All services operational
- `"degraded"` - Some services experiencing issues
- `"unhealthy"` - Critical services down

---

## Rate Limits
| Endpoint | Rate Limit | Time Window |
|----------|------------|-------------|
| `/upload` | 10 requests | 1 minute |
| `/chat` | 100 requests | 1 minute |
| `/health` | 1000 requests | 1 minute |

## Response Headers
All responses include:
```
Content-Type: application/json
X-Request-ID: unique-request-identifier
X-Response-Time-MS: processing-time-milliseconds
```

## WebSocket Support
*Note: WebSocket endpoints for real-time chat are planned for v2.0*

---

## Error Handling

### HTTP Status Codes
| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Access denied |
| 413 | Payload Too Large | File size exceeds limit |
| 422 | Unprocessable Entity | Invalid JSON schema |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server processing error |
| 503 | Service Unavailable | External service down |

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2026-02-07T14:30:00Z",
  "request_id": "req_123456789"
}
```

## API Versioning
- Current version: `v1`
- Version specified in URL path: `/api/v1/`
- Backward compatibility maintained for 12 months
- Deprecation notices provided 6 months in advance

## 🔧 Usage Examples

### 1. Document Upload & Processing

```python
import requests

# Upload a PDF with semantic chunking
with open("research_paper.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/upload",
        files={"uploaded_file": f},
        data={"chunking_strategy": "semantic"}
    )
print(response.json())
```

### 2. Conversational Chat

```python
import requests

# Start a conversation
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "query": "What are the key findings in the uploaded research paper?",
        "session_id": None  # Will generate new session
    }
)

chat_data = response.json()
print(f"AI Response: {chat_data['response']}")
print(f"Used {len(chat_data['sources'])} document sources")

# Continue conversation with same session
followup = requests.post(
    "http://localhost:8000/api/v1/chat", 
    json={
        "query": "Can you elaborate on the methodology?",
        "session_id": chat_data["session_id"]  # Continue session
    }
)
```

### 3. Interview Booking

```python
# Natural language booking request
booking_response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "query": "I'd like to book an interview. My name is Sarah Johnson, email sarah.j@email.com. Can we do tomorrow at 3 PM for a technical role?"
    }
)

booking_info = booking_response.json()["booking_info"]
if booking_info["booking_detected"]:
    print(f"Booking Status: {booking_info['booking_status']}")
    print(f"Extracted Info: {booking_info['extracted_info']}")
    if booking_info["booking_id"]:
        print(f"Booking saved with ID: {booking_info['booking_id']}")
```

## 🧠 Advanced Features

### TOON Format Optimization
The system uses **Token-Oriented Object Notation (TOON)** for ~40% more efficient LLM token usage:

```python
# Traditional JSON-like prompt (~100 tokens)
"""
Previous conversation:
{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]}
"""

# TOON format (~60 tokens) 
"""
history[2]{role,content}:
  user,Hello
  assistant,Hi there!
"""
```

### Hybrid Booking Extraction
Combines **spaCy NER** + **LLM reasoning** for maximum accuracy:
- **spaCy**: Excellent for names, emails, structured data
- **LLM**: Handles complex temporal expressions ("next Friday", "tomorrow at lunch")

### Multi-Turn Context
Redis-based session management maintains conversation context across interactions with automatic session UUID generation.

## 📊 Database Schema

### Documents Table
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_size INTEGER NOT NULL,
    doc_type VARCHAR NOT NULL, -- 'pdf' | 'txt'
    chunking_strat VARCHAR NOT NULL, -- 'fixed_size' | 'semantic'
    upload_date TIMESTAMP DEFAULT NOW(),
    total_chunk_count INTEGER DEFAULT 0
);
```

### Bookings Table
```sql
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,
    interview_type VARCHAR DEFAULT 'general',
    status VARCHAR DEFAULT 'pending',
    confidence_score FLOAT DEFAULT 0.0,
    extracted_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🧪 Testing

Run the built-in health check:
```bash
curl http://localhost:8000/api/v1/health
```

Test document upload:
```bash
echo "This is a test document." > test.txt
curl -X POST "http://localhost:8000/api/v1/upload" \
     -F "uploaded_file=@test.txt"
```

Test conversation:
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "Hello, what can you help me with?"}'
```

## 🚨 Troubleshooting

### Common Issues

**1. spaCy Model Missing:**
```bash
python -m spacy download en_core_web_sm
```

**2. Qdrant Connection Failed:**
```bash
# Check if Qdrant is running
curl http://localhost:6333/health
```

**3. Redis Connection Error:**
```bash
redis-cli ping  # Should return PONG
```

**4. Ollama Model Not Found:**
```bash
ollama pull llama3.2:1b
ollama list  # Verify model is installed
```

### Logs
Check application logs for detailed error information:
```bash
tail -f /var/log/rag-api.log
# Or check console output when running with --reload
```

## 🔒 Production Deployment

### Environment Variables
```bash
# Production database
DATABASE_URL=postgresql://user:pass@prod-db:5432/ragapi

# Security
CORS_ORIGINS=["https://yourapp.com"]  
API_RATE_LIMIT=100

# Performance  
QDRANT_URL=http://qdrant-cluster:6333
REDIS_URL=redis://redis-cluster:6379
```

### Docker Deployment
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN pip install -e .
RUN python -m spacy download en_core_web_sm

EXPOSE 8000
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## ⚡ Performance Optimization

### ONNX Runtime Optimization (Recommended for Production)

For **production deployments**, consider switching to pure ONNX runtime to dramatically reduce resource usage:

- **🏗️ Docker Image**: 78% smaller (800MB vs 3.5GB)
- **💾 Memory Usage**: 67% less (400MB vs 1.2GB)  
- **🚀 Cold Start**: 75% faster (3-5s vs 15-20s)
- **📦 Dependencies**: 92% fewer ML packages (160MB vs 2GB)

```bash
# One-time model conversion
python scripts/convert_to_onnx.py

# Switch to optimized runtime
pip install -r requirements.minimal.txt

# Use optimized Docker build
docker build -f Dockerfile.optimized -t rag-api:optimized .
```

📖 **Complete guide**: [ONNX_OPTIMIZATION.md](docs/ONNX_OPTIMIZATION.md)

## 📈 Performance

- **Document Processing**: ~2-5 seconds per PDF page
- **Vector Search**: <100ms for similarity queries (ONNX-optimized embeddings)
- **Chat Response**: 1-3 seconds (including LLM inference)
- **Booking Extraction**: <500ms (spaCy + LLM hybrid)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **Qdrant** for vector database capabilities  
- **spaCy** for industrial-strength NLP
- **Sentence Transformers** for embeddings
- **ONNX Runtime** for optimized ML inference
- **TOON** library for LLM token optimization

---

**Built with ❤️ for PalmMind Technology**