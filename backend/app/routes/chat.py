from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..query_engine import query_engine

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sql_query: Optional[str] = None
    results: Optional[List[dict]] = None
    query_type: Optional[str] = None
    highlighted_nodes: Optional[List[str]] = None


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a natural language query."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        result = await query_engine.process_query(request.message.strip())
        return ChatResponse(
            answer=result['answer'],
            sql_query=result.get('sql_query'),
            results=result.get('results', []),
            query_type=result.get('query_type'),
            highlighted_nodes=result.get('highlighted_nodes', [])
        )
    except Exception as e:
        print(f"Chat error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/clear")
async def clear_history():
    """Clear conversation history."""
    query_engine.conversation_history = []
    return {"status": "cleared"}