from fastapi import APIRouter
from pydantic import BaseModel
from app.services.retrieval_service import search

router = APIRouter()

class QueryRequest(BaseModel):
    question: str

@router.post("/query")
async def query_documents(request: QueryRequest):
    result = search(request.question, synthesize=True)
    return {"query": request.question, "response": result}