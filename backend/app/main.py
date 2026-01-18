from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.db.vector_store import vector_store, INDEX_FILE
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.query import router as query_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    
    # Load FAISS index if it exists
    if INDEX_FILE.exists():
        try:
            vector_store.load()
            print(f"✅ Loaded FAISS index with {vector_store.total_vectors} vectors")
        except Exception as e:
            print(f"⚠️  Warning: Could not load FAISS index: {e}")
            print("   Starting with empty index. It will be populated on first document upload.")
    else:
        print("ℹ️  No existing FAISS index found. Starting with empty index.")
    
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    description="""
    🤖 **AI Document Intelligence System**
    
    A production-ready RAG (Retrieval-Augmented Generation) system with:
    - 🔐 Multi-user authentication (JWT)
    - 📄 Document ingestion and processing
    - 🧠 Semantic search with FAISS
    - 💬 Context-aware Q&A with local LLM
    - 🤖 Agent-based reasoning with LangGraph
    - 📚 Complete source citations
    
    **Get Started:**
    1. Register a user at `/auth/register`
    2. Login at `/auth/login` to get your access token
    3. Upload documents at `/documents/upload`
    4. Query your documents at `/query` or `/query/agent`
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(query_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app_name": settings.APP_NAME, "env": settings.ENV}
