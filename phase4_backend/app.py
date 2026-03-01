from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Ensure the parent directory is in the path to import from phase3_rag_core
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from phase3_rag_core.rag import answer_query

app = FastAPI(title="Nextleap RAG Chatbot API")

# Add CORS so a frontend domain can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Nextleap Backend API is running."}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    result = answer_query(request.query)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return {
        "answer": result["answer"],
        "sources": result["sources"]
    }
