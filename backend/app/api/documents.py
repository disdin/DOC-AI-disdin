from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Optional
from bson import ObjectId

from app.services.ingestion import ingest_document
from app.services.auth_service import get_current_active_user
from app.models.user import UserInDB
from app.db.mongo import mongo_db

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Upload a document for ingestion (requires authentication).
    
    Accepts text files (.txt, .md) and processes them through the ingestion pipeline:
    - Chunks the document
    - Generates embeddings
    - Stores in FAISS vector store
    - Saves metadata in MongoDB (associated with user)
    """
    # Validate file type
    allowed_extensions = {".txt", ".md"}
    filename = file.filename or "unknown.txt"
    
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Read file content
    try:
        content = await file.read()
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Could not decode file. Please ensure it's a valid UTF-8 text file."
        )
    
    if not text_content.strip():
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )
    
    # Ingest the document (associated with current user)
    try:
        result = await ingest_document(
            filename=filename,
            content=text_content,
            user_email=current_user.email
        )
        return {
            "message": "Document uploaded and processed successfully",
            **result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("")
async def list_documents(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    List all documents uploaded by the current user.
    
    Returns a list of documents with their metadata.
    """
    try:
        # Query documents collection for user's documents
        documents_cursor = mongo_db.db.documents.find(
            {"user_email": current_user.email}
        ).sort("created_at", -1)
        
        documents = []
        async for doc in documents_cursor:
            documents.append({
                "id": str(doc["_id"]),
                "filename": doc["filename"],
                "chunk_count": doc.get("chunk_count", 0),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None
            })
        
        return {
            "documents": documents,
            "total": len(documents)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching documents: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Delete a specific document and all its chunks.
    
    Only the document owner can delete it.
    """
    try:
        # Validate ObjectId format
        try:
            doc_obj_id = ObjectId(document_id)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid document ID format"
            )
        
        # Find the document
        document = await mongo_db.db.documents.find_one({
            "_id": doc_obj_id,
            "user_email": current_user.email
        })
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found or you don't have permission to delete it"
            )
        
        # Delete all chunks associated with this document
        delete_chunks_result = await mongo_db.db.chunks.delete_many({
            "document_id": str(doc_obj_id)
        })
        
        # Delete the document
        await mongo_db.db.documents.delete_one({"_id": doc_obj_id})
        
        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "chunks_deleted": delete_chunks_result.deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )
