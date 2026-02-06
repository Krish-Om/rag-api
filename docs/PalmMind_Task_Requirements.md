# AI/ML Intern Task - Palm Mind Technology

## Task Overview

Build a **backend** with **two REST APIs** using **FastAPI** (or similar):

---

## API 1: Document Ingestion API

### Requirements:

1. **Upload .pdf or .txt files**

2. **Extract text** from uploaded documents

3. **Apply two chunking strategies** (selectable):
   - Fixed-size chunking
   - Semantic chunking
   - Other intelligent chunking methods

4. **Generate embeddings & store** in one of:
   - Pinecone
   - Qdrant
   - Weaviate
   - Milvus

5. **Save metadata** in SQL/NoSQL database:
   - Document ID
   - Filename
   - Upload timestamp
   - Chunking strategy used
   - Number of chunks
   - Other relevant metadata

---

## API 2: Conversational RAG API

### Requirements:

1. **Custom RAG** (no RetrievalQAChain)
   - Build your own retrieval logic

2. **Use Redis for chat memory**
   - Store conversation history
   - Maintain context across sessions

3. **Handle multi-turn queries**
   - Support contextual follow-up questions
   - Reference previous messages

4. **Support interview booking** (name, email, date, time) using LLM
   - Parse natural language booking requests
   - Extract structured information
   - Validate and store booking data

5. **Store booking info** in database

---

## Constraints

### ❌ Do NOT use:
- FAISS
- Chroma
- UI (No user interface required)
- RetrievalQAChain

### ✅ Must use:
- Pinecone, Qdrant, Weaviate, or Milvus for vector storage
- Clean modular code following industry standards
- Proper typing and annotations

---

## Submission Requirements

- **Submit via:** GitHub Link
- **Send to:** hr@palmmind.com (reply to this email)
- **Timeline:** At your earliest convenience

---

## Important Note

**Please undertake this task only IF:**
- You could commit at least 1 year with us, AND
- The notice period is 2 months IF selected

---

## Contact

**Pratima Giri**  
HR PalmMind Technology

Many Thanks & Regards

---

## Technical Implementation Checklist

### Setup
- [ ] Initialize FastAPI project
- [ ] Set up virtual environment
- [ ] Install required dependencies
- [ ] Configure environment variables

### API 1: Document Ingestion
- [ ] Create file upload endpoint
- [ ] Implement PDF text extraction
- [ ] Implement TXT file reading
- [ ] Build fixed-size chunking strategy
- [ ] Build semantic chunking strategy
- [ ] Integrate vector database (choose one: Pinecone/Qdrant/Weaviate/Milvus)
- [ ] Generate embeddings
- [ ] Store vectors in vector DB
- [ ] Set up metadata database (SQL/NoSQL)
- [ ] Store document metadata
- [ ] Add error handling
- [ ] Write API documentation

### API 2: Conversational RAG
- [ ] Set up Redis connection
- [ ] Implement chat memory storage
- [ ] Build custom RAG retrieval logic
- [ ] Create conversation endpoint
- [ ] Handle multi-turn conversations
- [ ] Implement LLM integration
- [ ] Build interview booking parser
- [ ] Extract booking information (name, email, date, time)
- [ ] Validate extracted data
- [ ] Store booking information
- [ ] Add session management
- [ ] Implement error handling
- [ ] Write API documentation

### Code Quality
- [ ] Add type hints throughout
- [ ] Follow PEP 8 standards
- [ ] Create modular, reusable code
- [ ] Add logging
- [ ] Write docstrings
- [ ] Create requirements.txt
- [ ] Write README.md
- [ ] Add .gitignore

### Testing & Documentation
- [ ] Test document upload
- [ ] Test both chunking strategies
- [ ] Test vector storage and retrieval
- [ ] Test conversation flow
- [ ] Test booking extraction
- [ ] Document API endpoints
- [ ] Create usage examples
- [ ] Prepare GitHub repository

---

## Recommended Tech Stack

- **Framework:** FastAPI
- **Vector Database:** Qdrant or Pinecone
- **Cache/Memory:** Redis
- **Metadata DB:** PostgreSQL or MongoDB
- **LLM:** OpenAI GPT-4 / GPT-3.5-turbo
- **Embeddings:** OpenAI embeddings or sentence-transformers
- **PDF Processing:** PyPDF2 or pdfplumber
- **Text Processing:** spaCy or NLTK (for semantic chunking)

---

## Deliverables

1. GitHub repository with complete code
2. README.md with:
   - Setup instructions
   - API documentation
   - Usage examples
   - Dependencies list
3. Clean, well-structured code
4. Proper error handling
5. Type annotations
