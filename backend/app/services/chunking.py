from typing import List
from dataclasses import dataclass


@dataclass
class Chunk:
    """Structured chunk with text and metadata."""
    text: str
    chunk_index: int
    start_char: int
    end_char: int


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Chunk]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: The input text to chunk
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of overlapping characters between chunks
        
    Returns:
        List of Chunk objects with text and metadata
    """
    if not text or not text.strip():
        return []
    
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        # Calculate end position
        end = start + chunk_size
        
        # If not at the end, try to break at a sentence or word boundary
        if end < len(text):
            # Try to find a sentence boundary (. ! ?)
            for boundary in ['. ', '! ', '? ', '\n\n', '\n']:
                boundary_pos = text.rfind(boundary, start, end)
                if boundary_pos != -1:
                    end = boundary_pos + len(boundary)
                    break
            else:
                # Fall back to word boundary (space)
                space_pos = text.rfind(' ', start, end)
                if space_pos != -1 and space_pos > start:
                    end = space_pos + 1
        else:
            end = len(text)
        
        # Extract chunk text
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunks.append(Chunk(
                text=chunk_text,
                chunk_index=chunk_index,
                start_char=start,
                end_char=end
            ))
            chunk_index += 1
        
        # Move start position with overlap
        start = end - chunk_overlap
        
        # Ensure we make progress
        if start <= chunks[-1].start_char if chunks else 0:
            start = end
    
    return chunks


def chunk_document(
    content: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[dict]:
    """
    Chunk a document and return as list of dictionaries.
    
    Args:
        content: Document text content
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunk dictionaries with text and metadata
    """
    chunks = chunk_text(content, chunk_size, chunk_overlap)
    return [
        {
            "text": chunk.text,
            "chunk_index": chunk.chunk_index,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char
        }
        for chunk in chunks
    ]
