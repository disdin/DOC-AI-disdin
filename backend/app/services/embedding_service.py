from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

# Using all-MiniLM-L6-v2: fast, small (80MB), 384 dimensions, good quality
MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    def __init__(self, model_name: str = MODEL_NAME):
        """Initialize the embedding service with a SentenceTransformer model."""
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of shape (len(texts), embedding_dimension)
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.astype(np.float32)

    def embed_single(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string to embed
            
        Returns:
            numpy array of shape (embedding_dimension,)
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)


# Global embedding service instance
embedding_service = EmbeddingService()
