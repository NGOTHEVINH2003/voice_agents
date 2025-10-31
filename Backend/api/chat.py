from fastapi import APIRouter
from pydantic import BaseModel
from Backend.services.rag_service import query_rag

router = APIRouter(prefix="/chat", tags=["Chat"])

class QueryRequest(BaseModel):
    question: str
    namespace: str = "default"
    top_k: int = None

@router.post("/query")
def query(req: QueryRequest):
    answer = query_rag(req.question)
    return {"answer": answer}
