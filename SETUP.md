# 🚀 Complete Setup Guide

This guide will walk you through setting up the AI Document Intelligence System on your machine.

## Table of Contents

- [Prerequisites Installation](#prerequisites-installation)
- [Project Setup](#project-setup)
- [Running the System](#running-the-system)
- [Verification](#verification)
- [Common Issues](#common-issues)

---

## Prerequisites Installation

### 1. Python 3.10+ Installation

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

#### macOS
```bash
# Using Homebrew
brew install python@3.10
```

#### Windows
Download and install from [python.org](https://www.python.org/downloads/)

**Verify installation:**
```bash
python3 --version  # Should show 3.10 or higher
```

---

### 2. MongoDB Installation

#### Option A: Local MongoDB

**Linux (Ubuntu/Debian)**
```bash
# Import MongoDB public GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -sc)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install MongoDB
sudo apt update
sudo apt install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

**macOS**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Windows**
1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Run the installer (choose "Complete" installation)
3. MongoDB will run as a Windows service

**Verify MongoDB is running:**
```bash
mongosh
# Should connect successfully
```

#### Option B: MongoDB Atlas (Cloud - Free Tier)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Sign up for a free account
3. Create a new cluster (free M0 tier)
4. Create a database user
5. Whitelist your IP address (or use 0.0.0.0/0 for development)
6. Get your connection string
7. Update `MONGO_URI` in your `.env` file with the Atlas connection string

---

### 3. Ollama Installation

Ollama runs local LLMs on your machine.

**Linux**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS**
```bash
# Download from website
# Or use brew
brew install ollama
```

**Windows**
Download installer from [ollama.ai](https://ollama.ai/download)

**Start Ollama:**
```bash
ollama serve  # Run in a separate terminal
```

**Pull the Mistral model:**
```bash
ollama pull mistral
```

Other available models:
- `ollama pull llama2` - Meta's LLaMA 2
- `ollama pull phi` - Microsoft's Phi-2 (smaller, faster)
- `ollama pull codellama` - Code-focused model

**Verify Ollama is working:**
```bash
ollama list  # Should show installed models
```

---

## Project Setup

### 1. Clone/Download the Project

```bash
cd ~
git clone <your-repo-url> doc-ai
cd doc-ai
```

Or if you have the files, extract them:
```bash
cd ~/doc-ai
```

### 2. Create Python Virtual Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Your prompt should now show (venv)
```

### 3. Install Python Dependencies

```bash
# Make sure venv is activated!
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (web framework)
- MongoDB drivers (Motor, PyMongo)
- FAISS (vector search)
- SentenceTransformers (embeddings)
- LangGraph (agent framework)
- JWT & password libraries
- And more...

**Installation may take 5-10 minutes** as it downloads models.

### 4. Configure Environment Variables

```bash
# Copy the example file
cp env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

**Minimal configuration for local setup:**
```bash
APP_NAME="AI Document Intelligence System"
ENV="development"

MONGO_URI="mongodb://localhost:27017"
MONGO_DB_NAME="doc_ai"

OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="mistral"

SECRET_KEY="change-this-to-a-random-32-character-string"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Generate a secure SECRET_KEY:**
```bash
openssl rand -hex 32
# Copy the output to SECRET_KEY
```

### 5. Create Required Directories

```bash
# From backend directory
mkdir -p faiss_index
```

---

## Running the System

You need **3 terminals** running simultaneously:

### Terminal 1: MongoDB

**If using local MongoDB:**
```bash
# Linux/macOS - if not running as service
mongod

# Or if installed as service, it should already be running
# Check with: sudo systemctl status mongod
```

**If using MongoDB Atlas:** Skip this step, it's already running in the cloud.

### Terminal 2: Ollama

```bash
ollama serve
```

Leave this running. You should see:
```
Ollama is running at http://localhost:11434
```

### Terminal 3: FastAPI Application

```bash
cd ~/doc-ai/backend

# Activate virtual environment
source venv/bin/activate  # On Linux/macOS
# venv\Scripts\activate   # On Windows

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
Connected to MongoDB: doc_ai
INFO:     Application startup complete.
```

---

## Verification

### 1. Check API is Running

Open your browser and visit: **http://localhost:8000/docs**

You should see the **Swagger UI** with all API endpoints.

### 2. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "app_name": "AI Document Intelligence System",
  "env": "development"
}
```

### 3. Check Ollama Integration

```bash
curl http://localhost:8000/query/health
```

Expected response:
```json
{
  "ollama_available": true,
  "model": "mistral",
  "status": "ready"
}
```

If `ollama_available` is `false`, check that:
1. Ollama is running (`ollama serve`)
2. Mistral model is pulled (`ollama pull mistral`)

### 4. Test the Complete Flow

#### Register a user:
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'
```

#### Login:
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123"
```

Save the `access_token` from the response.

#### Create a test document:
```bash
echo "Python is a high-level programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991." > test_doc.txt
```

#### Upload the document:
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -F "file=@test_doc.txt"
```

#### Query the document:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who created Python?",
    "k": 3
  }'
```

You should get an answer with source citations!

---

## Common Issues

### Issue: "Could not connect to MongoDB"

**Solution:**
```bash
# Check if MongoDB is running
sudo systemctl status mongod  # Linux
brew services list             # macOS

# Start if not running
sudo systemctl start mongod    # Linux
brew services start mongodb-community  # macOS

# Or run manually
mongod
```

### Issue: "Ollama not available"

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434

# If not, start it
ollama serve

# Verify model is pulled
ollama list
ollama pull mistral
```

### Issue: "Module not found" errors

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: "FAISS index not found"

**Solution:**
```bash
# Create the directory
mkdir -p faiss_index

# The index will be created automatically when you upload first document
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill the process or use a different port
uvicorn app.main:app --reload --port 8001
```

### Issue: Slow embeddings on first run

**Explanation:** SentenceTransformers downloads the model (~80MB) on first use.

**Solution:** Wait for the download to complete. Subsequent runs will be fast.

### Issue: Out of memory with large documents

**Solution:**
- Process documents in smaller chunks
- Reduce chunk size in `chunking.py`
- Use a smaller embedding model

---

## Next Steps

Once everything is working:

1. ✅ Read the [PROJECT_README.md](PROJECT_README.md) for API usage
2. ✅ Explore the Swagger UI at http://localhost:8000/docs
3. ✅ Try the agent-based queries at `/query/agent`
4. ✅ Upload your own documents and experiment!

---

## Production Deployment Notes

For production deployment:

1. **Security:**
   - Change `SECRET_KEY` to a strong random value
   - Use HTTPS (nginx, caddy, etc.)
   - Enable MongoDB authentication
   - Add rate limiting

2. **Performance:**
   - Use MongoDB indexes
   - Consider Redis for caching
   - Use IndexIVFFlat for large vector stores
   - Deploy Ollama on a GPU server

3. **Monitoring:**
   - Add logging (Sentry, CloudWatch, etc.)
   - Monitor MongoDB performance
   - Track API response times

---

**Need help?** Check the troubleshooting section or review the logs!

Happy building! 🚀
