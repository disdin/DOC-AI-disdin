# 📚 API Reference

Complete API documentation for the AI Document Intelligence System.

## Base URL

```
http://localhost:8000
```

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 📍 Endpoints

### Authentication

#### POST `/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"  // optional
}
```

**Response: `201 Created`**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `400` - Email already registered
- `422` - Invalid email format or missing required fields

---

#### POST `/auth/login`

Login to receive a JWT access token.

**Content-Type:** `application/x-www-form-urlencoded`

**Request Body:**
```
username=user@example.com&password=securepassword
```

**Response: `200 OK`**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `401` - Incorrect email or password

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword"
```

---

#### GET `/auth/me`

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response: `200 OK`**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `401` - Invalid or expired token

---

### Document Management

#### POST `/documents/upload`

Upload a document for ingestion and processing.

**Requires Authentication**

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: Text file (.txt or .md)

**Response: `200 OK`**
```json
{
  "message": "Document uploaded and processed successfully",
  "document_id": "507f1f77bcf86cd799439011",
  "filename": "document.txt",
  "chunks_processed": 15,
  "faiss_start_index": 0,
  "faiss_end_index": 15
}
```

**Errors:**
- `400` - Invalid file type or empty file
- `401` - Authentication required
- `500` - Processing error

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.txt"
```

---

### Search

#### GET `/search`

Semantic search across user's documents.

**Requires Authentication**

**Query Parameters:**
- `q` (required): Search query text
- `k` (optional, default=5): Number of results to return (1-20)

**Response: `200 OK`**
```json
{
  "query": "python programming",
  "results": [
    {
      "text": "Python is a high-level programming language...",
      "filename": "python_intro.txt",
      "document_id": "507f1f77bcf86cd799439011",
      "chunk_index": 2,
      "faiss_index": 10,
      "start_char": 500,
      "end_char": 1000,
      "distance": 0.8234,
      "relevance_score": 0.9206,
      "citation": "[1] python_intro.txt (Chunk 2, Chars 500-1000)"
    }
  ],
  "total_results": 5
}
```

**Errors:**
- `401` - Authentication required
- `422` - Invalid parameters

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/search?q=python%20programming&k=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Query (RAG)

#### POST `/query`

Linear RAG pipeline: Query → Retrieve → Generate answer.

**Requires Authentication**

**Request Body:**
```json
{
  "question": "What is Python?",
  "k": 5  // optional, default=5
}
```

**Response: `200 OK`**
```json
{
  "question": "What is Python?",
  "answer": "Python is a high-level, interpreted programming language created by Guido van Rossum. It emphasizes code readability and simplicity...",
  "sources": [
    {
      "text": "Python is a high-level programming language...",
      "filename": "python_intro.txt",
      "document_id": "507f1f77bcf86cd799439011",
      "chunk_index": 2,
      "start_char": 500,
      "end_char": 1000,
      "distance": 0.8234,
      "relevance_score": 0.9206,
      "citation": "[1] python_intro.txt (Chunk 2, Chars 500-1000)"
    }
  ]
}
```

**Errors:**
- `401` - Authentication required
- `503` - LLM service unavailable (check Ollama)

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Python?", "k": 5}'
```

---

#### POST `/query/agent`

Agent-based RAG pipeline with LangGraph: Retrieve → Reason → Answer.

**Requires Authentication**

**Request Body:**
```json
{
  "question": "Explain Python's key features",
  "k": 5  // optional, default=5
}
```

**Response: `200 OK`**
```json
{
  "question": "Explain Python's key features",
  "answer": "Python has several key features including simplicity, readability, extensive libraries...",
  "reasoning": "The retrieved context contains relevant information about Python's design philosophy and features. The information appears sufficient to provide a comprehensive answer.",
  "sources": [
    {
      "text": "Python emphasizes code readability...",
      "filename": "python_intro.txt",
      "document_id": "507f1f77bcf86cd799439011",
      "chunk_index": 3,
      "start_char": 1000,
      "end_char": 1500,
      "distance": 0.7123,
      "relevance_score": 0.9411,
      "citation": "[1] python_intro.txt (Chunk 3, Chars 1000-1500)"
    }
  ],
  "messages": [
    {
      "role": "human",
      "content": "Retrieved 5 relevant chunks for: Explain Python's key features"
    },
    {
      "role": "ai",
      "content": "Reasoning: The retrieved context contains..."
    },
    {
      "role": "ai",
      "content": "Python has several key features..."
    }
  ]
}
```

**Differences from `/query`:**
- Includes `reasoning` field with agent's analysis
- Includes `messages` field with agent's internal dialogue
- May provide more thoughtful answers due to reasoning step

**Errors:**
- `401` - Authentication required
- `500` - Agent execution failed

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/query/agent" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain Python features", "k": 5}'
```

---

#### GET `/query/health`

Check if the query pipeline dependencies are available.

**No Authentication Required**

**Response: `200 OK`**
```json
{
  "ollama_available": true,
  "model": "mistral",
  "status": "ready"
}
```

If Ollama is not available:
```json
{
  "ollama_available": false,
  "model": "mistral",
  "status": "ollama_unavailable"
}
```

---

### System

#### GET `/health`

Basic health check endpoint.

**No Authentication Required**

**Response: `200 OK`**
```json
{
  "status": "ok",
  "app_name": "AI Document Intelligence System",
  "env": "development"
}
```

---

## 🔑 Response Field Explanations

### Source/Citation Fields

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Chunk text (truncated to 200 chars for display) |
| `filename` | string | Original document filename |
| `document_id` | string | MongoDB document ID |
| `chunk_index` | integer | Chunk number within the document (0-indexed) |
| `start_char` | integer | Starting character position in original document |
| `end_char` | integer | Ending character position in original document |
| `distance` | float | L2 distance from query (lower = more similar) |
| `relevance_score` | float | 0-1 score (higher = more relevant), calculated as e^(-distance/10) |
| `citation` | string | Formatted citation for easy reference |

### Agent Message Roles

| Role | Description |
|------|-------------|
| `human` | System messages about agent actions |
| `ai` | Agent's reasoning and responses |

---

## 📊 HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created (e.g., new user) |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error in request data |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | External service (Ollama, MongoDB) unavailable |

---

## 🔒 Authentication Flow

### 1. Register
```bash
POST /auth/register
→ Returns user info (no token)
```

### 2. Login
```bash
POST /auth/login
→ Returns JWT token
→ Token expires in 30 minutes (configurable)
```

### 3. Use Token
```bash
Include in all subsequent requests:
Authorization: Bearer YOUR_TOKEN
```

### 4. Token Expiry
```bash
Token expires → Returns 401
→ Login again to get new token
```

---

## 💡 Best Practices

### 1. Chunking Strategy

Documents are automatically chunked:
- Default: 500 characters per chunk
- Overlap: 50 characters
- Smart boundaries: tries to break at sentences/paragraphs

**For better results:**
- Upload documents with clear structure
- Use markdown for formatted documents
- Split very large documents (>100K words) manually

### 2. Query Optimization

**Good queries:**
- "What is the main topic of this document?"
- "Explain the concept of X mentioned in the text"
- "List the key features of Y"

**Less effective queries:**
- Single word queries
- Very broad questions
- Questions about information not in documents

### 3. k Parameter Tuning

The `k` parameter determines how many chunks to retrieve:

- `k=3`: Fast, good for specific questions
- `k=5`: Default, balanced
- `k=10`: Comprehensive, better for broad questions
- `k=20`: Maximum, may include noise

### 4. Agent vs Linear Query

**Use `/query` when:**
- You want fast responses
- Query is straightforward
- You have limited compute resources

**Use `/query/agent` when:**
- You want more thoughtful answers
- Query is complex or multi-faceted
- You want to see the reasoning process
- You have sufficient compute resources

---

## 🧪 Testing with cURL

### Complete Workflow Example

```bash
# 1. Register
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# 2. Login and save token
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123" \
  | jq -r '.access_token')

echo $TOKEN

# 3. Upload document
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@mydoc.txt"

# 4. Search
curl -X GET "http://localhost:8000/search?q=python&k=3" \
  -H "Authorization: Bearer $TOKEN" \
  | jq

# 5. Query
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is this document about?"}' \
  | jq

# 6. Agent Query
curl -X POST "http://localhost:8000/query/agent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"Explain the main concepts"}' \
  | jq
```

---

## 🌐 Interactive Documentation

For interactive API testing, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide:
- Interactive request/response testing
- Auto-generated code samples
- Complete schema documentation
- Try-it-out functionality

---

## 📞 Rate Limits

Currently **no rate limiting** is implemented (development mode).

For production deployment, consider adding rate limiting:
- Per user: 100 requests/minute
- Per IP: 1000 requests/hour
- Document uploads: 10/hour per user

---

## 🔧 Configuration

API behavior can be configured via environment variables:

```bash
# Token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM model
OLLAMA_MODEL="mistral"  # or llama2, phi, etc.

# MongoDB connection
MONGO_URI="mongodb://localhost:27017"
```

---

**For more information, see [PROJECT_README.md](PROJECT_README.md) and [SETUP.md](SETUP.md)**
