from fastapi import FastAPI
from pydantic import BaseModel
from rag.query import query_rag

app = FastAPI(title="Voice Assistant - RAG API")

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query(req: QueryRequest):
    result = query_rag(req.question)
    return result
