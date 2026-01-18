from typing import List

from app.db.vector_store import vector_store
from app.services.embedding_service import embedding_service
from app.services.ingestion import get_chunks_by_faiss_indices


async def search_similar_chunks(query: str, k: int = 5, user_email: str = None) -> List[dict]:
    """
    Search for chunks similar to the query (filtered by user if provided).
    
    Args:
        query: The search query text
        k: Number of top results to return
        user_email: Optional user email to filter results (user-specific documents)
        
    Returns:
        List of chunk dictionaries with text and metadata, sorted by relevance
    """
    # Step 1: Embed the query
    query_embedding = embedding_service.embed_single(query)
    
    # Step 2: Search FAISS for nearest neighbors
    distances, indices = vector_store.search(query_embedding, k=k)
    
    # Step 3: Filter out invalid indices (-1 means no result)
    valid_indices = [int(idx) for idx in indices[0] if idx != -1]
    valid_distances = [float(dist) for idx, dist in zip(indices[0], distances[0]) if idx != -1]
    
    if not valid_indices:
        return []
    
    # Step 4: Retrieve chunk metadata from MongoDB (filtered by user if specified)
    chunks = await get_chunks_by_faiss_indices(valid_indices, user_email=user_email)
    
    # Step 5: Create a mapping of faiss_index to chunk
    chunk_map = {chunk["faiss_index"]: chunk for chunk in chunks}
    
    # Step 6: Build results in order of relevance (same order as FAISS returned)
    results = []
    for idx, distance in zip(valid_indices, valid_distances):
        if idx in chunk_map:
            chunk = chunk_map[idx]
            results.append({
                "text": chunk["text"],
                "filename": chunk["filename"],
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "faiss_index": chunk["faiss_index"],
                "start_char": chunk["start_char"],
                "end_char": chunk["end_char"],
                "distance": distance,  # L2 distance (lower = more similar)
            })
    
    return results
