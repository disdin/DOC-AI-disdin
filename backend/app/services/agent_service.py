from typing import List, TypedDict, Annotated
from operator import add

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from app.services.retrieval import search_similar_chunks
from app.services.llm_service import llm_service


class AgentState(TypedDict):
    """State that flows through the agent graph."""
    question: str
    retrieved_chunks: List[dict]
    reasoning: str
    answer: str
    messages: Annotated[List[BaseMessage], add]
    k: int  # Number of chunks to retrieve
    user_email: str  # User email for filtering documents


async def retrieve_node(state: AgentState) -> AgentState:
    """
    Node 1: Retrieve relevant chunks from vector store (user-specific).
    
    Takes the user question and retrieves the top-k relevant document chunks
    from the user's documents.
    """
    question = state["question"]
    k = state.get("k", 5)
    user_email = state.get("user_email")
    
    # Retrieve chunks using semantic search (user-specific)
    chunks = await search_similar_chunks(query=question, k=k, user_email=user_email)
    
    # Filter chunks by relevance threshold
    # Distance < 1.2 indicates semantic similarity (lower = better)
    RELEVANCE_THRESHOLD = 1.2
    relevant_chunks = [c for c in chunks if c.get("distance", 999) < RELEVANCE_THRESHOLD]
    
    # Update state with relevant chunks only
    state["retrieved_chunks"] = relevant_chunks
    
    if relevant_chunks:
        state["messages"] = state.get("messages", []) + [
            HumanMessage(content=f"Retrieved {len(relevant_chunks)} relevant chunks (filtered from {len(chunks)} total) for: {question}")
        ]
    else:
        state["messages"] = state.get("messages", []) + [
            HumanMessage(content=f"No relevant chunks found for: {question}. All {len(chunks)} retrieved chunks were below relevance threshold.")
        ]
    
    return state


async def reason_node(state: AgentState) -> AgentState:
    """
    Node 2: Reason about the retrieved information.
    
    Analyzes the retrieved chunks and determines if they contain
    sufficient information to answer the question.
    """
    question = state["question"]
    chunks = state["retrieved_chunks"]
    
    if not chunks:
        reasoning = "No relevant documents found to answer the question."
        state["reasoning"] = reasoning
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=reasoning)
        ]
        return state
    
    # Build a summary of retrieved information for reasoning
    context_summary = "\n".join([
        f"Chunk {i+1} (from {chunk['filename']}): {chunk['text'][:150]}..."
        for i, chunk in enumerate(chunks[:3])  # Show first 3 chunks
    ])
    
    reasoning_prompt = f"""Analyze the following retrieved information to determine if it can answer the question.

Question: {question}

Retrieved Context:
{context_summary}

Does this context contain relevant information to answer the question? Briefly explain."""
    
    try:
        reasoning = await llm_service.generate(
            prompt=reasoning_prompt,
            context=None,  # Don't add extra context for reasoning
            temperature=0.3,  # Lower temperature for more focused reasoning
            max_tokens=200
        )
    except Exception:
        reasoning = "Retrieved context appears relevant based on semantic similarity."
    
    state["reasoning"] = reasoning
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=f"Reasoning: {reasoning}")
    ]
    
    return state


async def answer_node(state: AgentState) -> AgentState:
    """
    Node 3: Generate the final answer.
    
    Uses the retrieved chunks and reasoning to generate a comprehensive answer.
    """
    question = state["question"]
    chunks = state["retrieved_chunks"]
    reasoning = state.get("reasoning", "")
    
    if not chunks:
        answer = "I couldn't find any relevant information in the uploaded documents to answer your question."
        state["answer"] = answer
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=answer)
        ]
        return state
    
    # Extract context texts for final answer generation
    context_texts = [chunk["text"] for chunk in chunks]
    
    # Generate answer with enhanced prompt that includes reasoning
    enhanced_prompt = f"""{question}

Note: {reasoning}"""
    
    try:
        answer = await llm_service.generate(
            prompt=enhanced_prompt,
            context=context_texts,
            temperature=0.7,
            max_tokens=512
        )
    except Exception as e:
        answer = f"Error generating answer: {str(e)}"
    
    state["answer"] = answer
    state["messages"] = state.get("messages", []) + [
        AIMessage(content=answer)
    ]
    
    return state


# Build the agent graph
def create_agent_graph():
    """Create and compile the LangGraph agent."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("generate", answer_node)
    
    # Define the flow: retrieve → reason → generate
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "reason")
    workflow.add_edge("reason", "generate")
    workflow.add_edge("generate", END)
    
    # Compile the graph
    return workflow.compile()


# Global agent instance
agent_graph = create_agent_graph()


async def run_agent(question: str, k: int = 5, user_email: str = None) -> dict:
    """
    Run the agent graph to answer a question (user-specific).
    
    Args:
        question: The user's question
        k: Number of chunks to retrieve
        user_email: User email for filtering documents
        
    Returns:
        Dictionary with answer, reasoning, sources, and messages
    """
    # Initialize state
    initial_state = {
        "question": question,
        "retrieved_chunks": [],
        "reasoning": "",
        "answer": "",
        "messages": [],
        "k": k,
        "user_email": user_email
    }
    
    # Run the agent graph
    final_state = await agent_graph.ainvoke(initial_state)
    
    return {
        "question": question,
        "answer": final_state["answer"],
        "reasoning": final_state["reasoning"],
        "sources": final_state["retrieved_chunks"],
        "messages": [
            {"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
            for m in final_state["messages"]
        ]
    }
