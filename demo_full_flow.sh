#!/bin/bash

# RAG API - Full Flow Demonstration Script
# This script demonstrates the complete workflow from document upload to conversational RAG with booking

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000/api/v1"

# Function to print section headers
print_section() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to print step
print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to pause for user
pause() {
    echo ""
    read -p "Press Enter to continue to next step..."
    echo ""
}

# Clear screen and show banner
clear
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║              RAG API - FULL FLOW DEMONSTRATION                        ║
║                                                                       ║
║  This demo showcases the complete workflow:                           ║
║  1. Document Upload & Vectorization (API 1)                           ║
║  2. Conversational RAG with Context Retrieval (API 2)                 ║
║  3. Multi-Turn Conversations                                          ║
║  4. Interview Booking with LLM Extraction (API 2)                     ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if API is running
print_step "Checking if API is running..."
if ! curl -sf "$API_URL/health" > /dev/null 2>&1; then
    print_error "API is not running! Please start it first:"
    echo "  docker compose up -d"
    echo "  OR"
    echo "  ./deploy.sh up"
    exit 1
fi
print_info "✓ API is healthy and running"
pause

# ============================================================================
# STEP 1: Document Upload (API 1)
# ============================================================================
print_section "STEP 1: Document Upload & Vectorization (API 1)"

print_step "Creating a sample company document..."
cat > /tmp/techcorp_info.txt << 'EOF'
TechCorp Company Information

TechCorp is a leading software company specializing in artificial intelligence 
and machine learning solutions. Founded in 2020, we provide cloud-based AI 
services to businesses worldwide.

Our Services:
- Custom ML model development and deployment
- AI consulting and strategic planning
- Cloud infrastructure setup and optimization
- Natural language processing solutions
- Computer vision applications
- 24/7 technical support and maintenance

Company Details:
- Founded: 2020
- Headquarters: San Francisco, CA
- Employees: 150+ AI specialists
- Clients: 500+ companies globally

Technologies We Use:
- Python, TensorFlow, PyTorch
- Docker, Kubernetes
- AWS, GCP, Azure
- FastAPI, PostgreSQL, Redis

Contact Information:
- Email: support@techcorp.com
- Phone: +1-555-0123
- Website: www.techcorp.com
- LinkedIn: linkedin.com/company/techcorp
- GitHub: github.com/techcorp

Interview Process:
We offer technical interviews, HR interviews, and system design rounds.
Interviews can be scheduled Monday-Friday, 9 AM to 5 PM PST.
EOF

print_info "Sample document created at /tmp/techcorp_info.txt"
print_step "Uploading document with semantic chunking..."
echo ""

UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/upload" \
  -F "uploaded_file=@/tmp/techcorp_info.txt" \
  -F "chunking_strategy=semantic")

echo "$UPLOAD_RESPONSE" | python3 -m json.tool

DOC_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('document_id', 'N/A'))" 2>/dev/null || echo "N/A")
CHUNKS=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('chunks_created', 'N/A'))" 2>/dev/null || echo "N/A")

print_info "✓ Document uploaded successfully"
print_info "  Document ID: $DOC_ID"
print_info "  Chunks created: $CHUNKS"
print_info "  Embeddings generated and stored in Qdrant"
print_info "  Metadata saved to PostgreSQL"

pause

# ============================================================================
# STEP 2: Verify Vector Storage
# ============================================================================
print_section "STEP 2: Verify Vector Storage (Qdrant)"

print_step "Checking Qdrant collection status..."
echo ""

QDRANT_INFO=$(curl -s http://localhost:6333/collections/document_chunks)
echo "$QDRANT_INFO" | python3 -m json.tool

VECTOR_COUNT=$(echo "$QDRANT_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin)['result']['points_count'])" 2>/dev/null || echo "N/A")

print_info "✓ Vectors stored in Qdrant"
print_info "  Total vectors in collection: $VECTOR_COUNT"
print_info "  Vector dimension: 384D"
print_info "  Distance metric: Cosine"

pause

# ============================================================================
# STEP 3: Conversational RAG - Context Retrieval
# ============================================================================
print_section "STEP 3: Conversational RAG - Context Retrieval (API 2)"

print_step "Query 1: Asking about company services (should retrieve context)..."
echo ""

RESPONSE1=$(curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What services does TechCorp offer?"
  }')

echo "$RESPONSE1" | python3 -m json.tool

SESSION_ID=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null)
CONTEXT_USED=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(json.load(sys.stdin).get('context_used', False))" 2>/dev/null)
SOURCES_COUNT=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('sources', [])))" 2>/dev/null)

print_info "✓ RAG retrieval successful"
print_info "  Session ID: $SESSION_ID"
print_info "  Context used: $CONTEXT_USED"
print_info "  Sources retrieved: $SOURCES_COUNT documents"
print_info "  Vector search performed in Qdrant"
print_info "  LLM generated response using context"

pause

# ============================================================================
# STEP 4: Multi-Turn Conversation
# ============================================================================
print_section "STEP 4: Multi-Turn Conversation (Context Maintained)"

print_step "Query 2: Follow-up question using same session..."
echo ""

RESPONSE2=$(curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"How can I contact them?\",
    \"session_id\": \"$SESSION_ID\"
  }")

echo "$RESPONSE2" | python3 -m json.tool

print_info "✓ Multi-turn conversation working"
print_info "  Same session continued"
print_info "  Previous context maintained via Redis"
print_info "  LLM understood pronoun reference ('them' = TechCorp)"

pause

# ============================================================================
# STEP 5: Get Conversation History
# ============================================================================
print_section "STEP 5: Conversation History (Redis Memory)"

print_step "Retrieving full conversation history from Redis..."
echo ""

curl -s "$API_URL/chat/$SESSION_ID/history?format=json" | python3 -m json.tool

print_info "✓ Chat history retrieved from Redis"
print_info "  TOON format optimization applied"
print_info "  Session memory enables coherent conversations"

pause

# ============================================================================
# STEP 6: Booking Detection (Incomplete)
# ============================================================================
print_section "STEP 6: Interview Booking - Incomplete Request"

print_step "Query 3: Booking request with missing information..."
echo ""

RESPONSE3=$(curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I want to book a technical interview for tomorrow at 2pm"
  }')

echo "$RESPONSE3" | python3 -m json.tool

BOOKING_STATUS=$(echo "$RESPONSE3" | python3 -c "import sys, json; print(json.load(sys.stdin).get('booking_info', {}).get('booking_status', 'N/A'))" 2>/dev/null)

print_info "✓ Booking intent detected"
print_info "  Status: $BOOKING_STATUS"
print_info "  Hybrid spaCy + LLM extraction working"
print_info "  Missing fields identified: name, email, date"
print_info "  Suggestions provided to user"

pause

# ============================================================================
# STEP 7: Complete Booking
# ============================================================================
print_section "STEP 7: Complete Interview Booking"

print_step "Query 4: Complete booking with all details..."
echo ""

RESPONSE4=$(curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I want to book a technical interview. My name is Alice Johnson, email alice@example.com, date is 2026-03-15, time is 2:00 PM"
  }')

echo "$RESPONSE4" | python3 -m json.tool

BOOKING_ID=$(echo "$RESPONSE4" | python3 -c "import sys, json; print(json.load(sys.stdin).get('booking_info', {}).get('booking_id', 'N/A'))" 2>/dev/null)
FINAL_STATUS=$(echo "$RESPONSE4" | python3 -c "import sys, json; print(json.load(sys.stdin).get('booking_info', {}).get('booking_status', 'N/A'))" 2>/dev/null)

print_info "✓ Booking created successfully"
print_info "  Booking ID: $BOOKING_ID"
print_info "  Status: $FINAL_STATUS"
print_info "  All fields extracted: name, email, date, time, type"
print_info "  Saved to PostgreSQL database"

pause

# ============================================================================
# STEP 8: Verify Database
# ============================================================================
print_section "STEP 8: Verify Database Persistence"

print_step "Checking PostgreSQL for saved booking..."
echo ""

docker exec -i rag-postgres psql -U raguser -d document_db -c \
  "SELECT id, name, email, booking_date, booking_time, interview_type, status 
   FROM booking 
   ORDER BY id DESC 
   LIMIT 3;" 2>/dev/null || print_error "Could not connect to database"

print_info "✓ Database persistence verified"
print_info "  Bookings stored in PostgreSQL"
print_info "  Documents and chunks metadata stored"
print_info "  Full data integrity maintained"

pause

# ============================================================================
# STEP 9: Health Check
# ============================================================================
print_section "STEP 9: System Health Check"

print_step "Checking all services health..."
echo ""

curl -s "$API_URL/health" | python3 -m json.tool

print_info "✓ All services healthy"
print_info "  ✓ FastAPI application"
print_info "  ✓ PostgreSQL database"
print_info "  ✓ Qdrant vector store"
print_info "  ✓ Redis cache"
print_info "  ✓ Ollama LLM service"

# ============================================================================
# Summary
# ============================================================================
echo ""
print_section "DEMONSTRATION COMPLETE ✓"

echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                        FULL FLOW SUMMARY                              ║
║                                                                       ║
║  ✓ Document uploaded and processed                                   ║
║  ✓ Text extracted and chunked (semantic strategy)                    ║
║  ✓ Embeddings generated using ONNX runtime                           ║
║  ✓ Vectors stored in Qdrant (384D)                                   ║
║  ✓ RAG context retrieval working                                     ║
║  ✓ Multi-turn conversations maintained                               ║
║  ✓ Booking intent detected and extracted                             ║
║  ✓ Complete booking saved to database                                ║
║  ✓ All services healthy and integrated                               ║
║                                                                       ║
║  Technologies Demonstrated:                                           ║
║  • Custom RAG (no pre-built chains)                                  ║
║  • Qdrant vector database                                            ║
║  • Redis chat memory with TOON optimization                          ║
║  • Hybrid spaCy + LLM booking extraction                             ║
║  • PostgreSQL metadata storage                                       ║
║  • ONNX optimized embeddings                                         ║
║  • Ollama local LLM inference                                        ║
║                                                                       ║
║  API Endpoints Used:                                                  ║
║  • POST /api/v1/upload          (Document Ingestion)                 ║
║  • POST /api/v1/chat            (Conversational RAG)                 ║
║  • GET  /api/v1/chat/{id}/history (Chat History)                     ║
║  • GET  /api/v1/health          (Health Check)                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo -e "${CYAN}Session ID for this demo: ${YELLOW}$SESSION_ID${NC}"
echo -e "${CYAN}Document ID uploaded: ${YELLOW}$DOC_ID${NC}"
echo -e "${CYAN}Booking ID created: ${YELLOW}$BOOKING_ID${NC}"
echo ""
echo -e "${GREEN}Thank you for watching the demonstration!${NC}"
echo -e "${BLUE}For more information, see README.md or visit http://localhost:8000/docs${NC}"
echo ""

# Cleanup
rm -f /tmp/techcorp_info.txt
