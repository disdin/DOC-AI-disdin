from typing import List, Optional
import math

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from app.services.retrieval import search_similar_chunks
from app.services.llm_service import llm_service
from app.services.agent_service import run_agent
from app.services.auth_service import get_current_active_user
from app.models.user import UserInDB

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    k: int = 5  # Number of chunks to retrieve


class SourceChunk(BaseModel):
    text: str
    filename: str
    document_id: str
    chunk_index: int
    start_char: int
    end_char: int
    distance: float
    relevance_score: float  # 0-1, higher is more relevant
    citation: str  # Formatted citation string


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceChunk]


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentQueryResponse(BaseModel):
    question: str
    answer: str
    reasoning: str
    sources: List[SourceChunk]
    messages: List[AgentMessage]


def build_citation(chunk: dict, rank: int) -> SourceChunk:
    """
    Build an enhanced citation with metadata and formatting.
    
    Args:
        chunk: Chunk dictionary from retrieval
        rank: Rank/position in results (1-indexed)
        
    Returns:
        SourceChunk with enhanced citation information
    """
    # Calculate relevance score from L2 distance
    # Lower distance = higher relevance
    # Using exponential decay: score = e^(-distance/10)
    relevance_score = math.exp(-chunk["distance"] / 10.0)
    relevance_score = min(1.0, max(0.0, relevance_score))  # Clamp to [0, 1]
    
    # Format citation string
    citation = f"[{rank}] {chunk['filename']} (Chunk {chunk['chunk_index']}, Chars {chunk['start_char']}-{chunk['end_char']})"
    
    # Truncate text for display
    display_text = chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
    
    return SourceChunk(
        text=display_text,
        filename=chunk["filename"],
        document_id=chunk["document_id"],
        chunk_index=chunk["chunk_index"],
        start_char=chunk["start_char"],
        end_char=chunk["end_char"],
        distance=chunk["distance"],
        relevance_score=round(relevance_score, 4),
        citation=citation
    )


@router.post("", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Full RAG Pipeline: Query → Retrieve → Generate (user-specific).
    
    1. Embeds the user question
    2. Retrieves top-k relevant chunks from user's documents in FAISS
    3. Passes context to LLM (Ollama)
    4. Returns generated answer with source citations
    """
    # Step 1: Retrieve relevant chunks (user-specific)
    chunks = await search_similar_chunks(query=request.question, k=request.k, user_email=current_user.email)
    
    if not chunks:
        return QueryResponse(
            question=request.question,
            answer="I couldn't find any relevant information in the uploaded documents to answer your question.",
            sources=[]
        )
    
    # Step 1.5: Check relevance threshold
    # Filter chunks with distance < 1.2 (lower distance = more similar)
    # Distance > 1.2 typically means chunks are not semantically related
    RELEVANCE_THRESHOLD = 1.2
    relevant_chunks = [c for c in chunks if c["distance"] < RELEVANCE_THRESHOLD]
    
    if not relevant_chunks:
        # Return early with explanation - all chunks are too dissimilar
        return QueryResponse(
            question=request.question,
            answer=f"I couldn't find relevant information about '{request.question}' in your uploaded documents. Your documents appear to contain different topics. Please try asking about the actual content of your uploaded files.",
            sources=[]
        )
    
    # Use only relevant chunks for context
    chunks = relevant_chunks
    
    # Step 2: Extract context texts for LLM
    context_texts = [chunk["text"] for chunk in chunks]
    
    # Step 3: Generate answer using LLM
    try:
        answer = await llm_service.generate(
            prompt=request.question,
            context=context_texts
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM service unavailable. Make sure Ollama is running. Error: {str(e)}"
        )
    
    # Step 4: Build enhanced source citations
    sources = [
        build_citation(chunk, rank=i+1)
        for i, chunk in enumerate(chunks)
    ]
    
    return QueryResponse(
        question=request.question,
        answer=answer,
        sources=sources
    )


@router.post("/agent", response_model=AgentQueryResponse)
async def query_documents_with_agent(
    request: QueryRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Agent-based RAG Pipeline using LangGraph: retrieve → reason → answer (user-specific).
    
    1. Retrieve: Embeds question and retrieves top-k relevant chunks from user's documents
    2. Reason: Analyzes retrieved information and determines relevance
    3. Answer: Generates final answer using LLM with context
    
    Returns answer with reasoning trace, sources, and agent messages.
    """
    try:
        result = await run_agent(question=request.question, k=request.k, user_email=current_user.email)
        
        # Build enhanced source citations
        sources = [
            build_citation(chunk, rank=i+1)
            for i, chunk in enumerate(result["sources"])
        ]
        
        return AgentQueryResponse(
            question=result["question"],
            answer=result["answer"],
            reasoning=result["reasoning"],
            sources=sources,
            messages=[AgentMessage(**msg) for msg in result["messages"]]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}"
        )


@router.get("/health")
async def query_health():
    """Check if the RAG pipeline dependencies are available."""
    ollama_ok = await llm_service.health_check()
    
    return {
        "ollama_available": ollama_ok,
        "model": llm_service.model,
        "status": "ready" if ollama_ok else "ollama_unavailable"
    }
