from typing import List, Optional

import httpx

from app.core.config import settings


class LLMService:
    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        model: str = settings.OLLAMA_MODEL
    ):
        """Initialize the LLM service for Ollama."""
        self.base_url = base_url
        self.model = model
        self.generate_url = f"{base_url}/api/generate"

    async def generate(
        self,
        prompt: str,
        context: Optional[List[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user's question/prompt
            context: List of relevant context chunks
            temperature: Creativity (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        # Build the full prompt with context
        full_prompt = self._build_prompt(prompt, context)
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.generate_url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

    def _build_prompt(self, question: str, context: Optional[List[str]] = None) -> str:
        """Build a RAG-style prompt with context."""
        if not context:
            return question
        
        # Format context with document markers
        context_text = "\n\n".join([f"[Document {i+1}]:\n{text}" for i, text in enumerate(context)])
        
        prompt = f"""You are a helpful AI assistant. Answer the question based ONLY on the provided context from the user's documents.

Context from documents:
{context_text}

Question: {question}

IMPORTANT RULES:
1. ONLY use information from the context above
2. If the context doesn't contain relevant information to answer the question, say: "I don't have information about this in your uploaded documents."
3. Do NOT use your general knowledge if it's not in the context
4. Always cite which document section you're using when answering
5. If the context seems unrelated to the question, explicitly say so

Answer:"""
        
        return prompt

    async def health_check(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "").split(":")[0] for m in models]
                    return self.model in model_names
                return False
        except Exception:
            return False


# Global LLM service instance
llm_service = LLMService()
