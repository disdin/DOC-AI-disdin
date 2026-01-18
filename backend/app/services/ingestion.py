from typing import List, Optional
from datetime import datetime

import numpy as np

from app.db.mongo import mongo_db
from app.db.vector_store import vector_store
from app.services.chunking import chunk_document
from app.services.embedding_service import embedding_service


async def ingest_document(
    filename: str,
    content: str,
    user_email: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> dict:
    """
    Ingest a document: chunk → embed → store in FAISS → save metadata in MongoDB.
    
    Args:
        filename: Name of the document
        content: Text content of the document
        user_email: Email of the user who owns this document
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        Dictionary with document_id and number of chunks processed
    """
    # Step 1: Chunk the document
    chunks = chunk_document(content, chunk_size, chunk_overlap)
    
    if not chunks:
        raise ValueError("Document produced no chunks")
    
    # Step 2: Get the starting index for FAISS (to map back to chunks later)
    start_index = vector_store.total_vectors
    
    # Step 3: Generate embeddings for all chunks
    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_texts(chunk_texts)
    
    # Step 4: Add embeddings to FAISS
    vector_store.add_vectors(embeddings)
    
    # Step 5: Save the FAISS index
    vector_store.save()
    
    # Step 6: Save document metadata to MongoDB (with user ownership)
    document_record = {
        "filename": filename,
        "user_email": user_email,
        "content_length": len(content),
        "chunk_count": len(chunks),
        "faiss_start_index": start_index,
        "faiss_end_index": start_index + len(chunks),
        "created_at": datetime.utcnow(),
    }
    
    result = await mongo_db.db.documents.insert_one(document_record)
    document_id = str(result.inserted_id)
    
    # Step 7: Save chunk metadata to MongoDB (with user ownership)
    chunk_records = []
    for i, chunk in enumerate(chunks):
        chunk_records.append({
            "document_id": document_id,
            "user_email": user_email,
            "filename": filename,
            "chunk_index": chunk["chunk_index"],
            "faiss_index": start_index + i,
            "text": chunk["text"],
            "start_char": chunk["start_char"],
            "end_char": chunk["end_char"],
            "created_at": datetime.utcnow(),
        })
    
    await mongo_db.db.chunks.insert_many(chunk_records)
    
    return {
        "document_id": document_id,
        "filename": filename,
        "chunks_processed": len(chunks),
        "faiss_start_index": start_index,
        "faiss_end_index": start_index + len(chunks),
    }


async def get_chunk_by_faiss_index(faiss_index: int) -> Optional[dict]:
    """Retrieve chunk metadata by FAISS index."""
    chunk = await mongo_db.db.chunks.find_one({"faiss_index": faiss_index})
    if chunk:
        chunk["_id"] = str(chunk["_id"])
    return chunk


async def get_chunks_by_faiss_indices(faiss_indices: List[int], user_email: str = None) -> List[dict]:
    """
    Retrieve multiple chunks by their FAISS indices.
    
    Args:
        faiss_indices: List of FAISS indices to retrieve
        user_email: Optional user email to filter chunks (user-specific documents)
        
    Returns:
        List of chunk dictionaries
    """
    # Build query filter
    query_filter = {"faiss_index": {"$in": faiss_indices}}
    
    # Add user filter if specified
    if user_email:
        query_filter["user_email"] = user_email
    
    chunks = []
    cursor = mongo_db.db.chunks.find(query_filter)
    async for chunk in cursor:
        chunk["_id"] = str(chunk["_id"])
        chunks.append(chunk)
    return chunks
