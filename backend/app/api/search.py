from typing import List, Optional
import math

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

from app.services.retrieval import search_similar_chunks
from app.services.auth_service import get_current_active_user
from app.models.user import UserInDB

router = APIRouter(prefix="/search", tags=["search"])


class SearchResult(BaseModel):
    text: str
    filename: str
    document_id: str
    chunk_index: int
    faiss_index: int
    start_char: int
    end_char: int
    distance: float
    relevance_score: float
    citation: str


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int


def build_search_result(chunk: dict, rank: int) -> SearchResult:
    """Build an enhanced search result with citation metadata."""
    # Calculate relevance score from L2 distance
    relevance_score = math.exp(-chunk["distance"] / 10.0)
    relevance_score = min(1.0, max(0.0, relevance_score))
    
    # Format citation
    citation = f"[{rank}] {chunk['filename']} (Chunk {chunk['chunk_index']}, Chars {chunk['start_char']}-{chunk['end_char']})"
    
    return SearchResult(
        text=chunk["text"],
        filename=chunk["filename"],
        document_id=chunk["document_id"],
        chunk_index=chunk["chunk_index"],
        faiss_index=chunk["faiss_index"],
        start_char=chunk["start_char"],
        end_char=chunk["end_char"],
        distance=chunk["distance"],
        relevance_score=round(relevance_score, 4),
        citation=citation
    )


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query text"),
    k: int = Query(5, ge=1, le=20, description="Number of results to return"),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Search for relevant document chunks using semantic similarity (user-specific).
    
    - Requires authentication
    - Embeds the query using SentenceTransformers
    - Performs FAISS similarity search
    - Returns top-k most relevant chunks from user's documents with enhanced citations
    """
    results = await search_similar_chunks(query=q, k=k, user_email=current_user.email)
    
    # Build enhanced search results with citations
    enhanced_results = [
        build_search_result(chunk, rank=i+1)
        for i, chunk in enumerate(results)
    ]
    
    return SearchResponse(
        query=q,
        results=enhanced_results,
        total_results=len(results)
    )
