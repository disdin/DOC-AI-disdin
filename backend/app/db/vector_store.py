import os
from pathlib import Path

import faiss
import numpy as np

# Default embedding dimension (will be set properly when embedding service is ready)
DEFAULT_DIMENSION = 384

# Default path for saving/loading the index
INDEX_DIR = Path("faiss_index")
INDEX_FILE = INDEX_DIR / "index.faiss"


class VectorStore:
    def __init__(self, dimension: int = DEFAULT_DIMENSION):
        """Initialize FAISS vector store with given dimension."""
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)

    def add_vectors(self, vectors: np.ndarray):
        """Add vectors to the index."""
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension {vectors.shape[1]} doesn't match index dimension {self.dimension}")
        self.index.add(vectors.astype(np.float32))

    def search(self, query_vector: np.ndarray, k: int = 5):
        """Search for k nearest neighbors."""
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        distances, indices = self.index.search(query_vector.astype(np.float32), k)
        return distances, indices

    def save(self, path: Path = INDEX_FILE):
        """Save the index to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path))
        print(f"FAISS index saved to {path}")

    def load(self, path: Path = INDEX_FILE):
        """Load the index from disk."""
        if not path.exists():
            raise FileNotFoundError(f"Index file not found: {path}")
        self.index = faiss.read_index(str(path))
        self.dimension = self.index.d
        print(f"FAISS index loaded from {path}")

    @property
    def total_vectors(self) -> int:
        """Return the total number of vectors in the index."""
        return self.index.ntotal


# Global vector store instance
vector_store = VectorStore()
