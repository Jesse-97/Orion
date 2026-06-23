from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload_routes, query_routes

app = FastAPI(title="LexRAG", description="Legal Document Intelligence System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_routes.router, prefix="/api")
app.include_router(query_routes.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "LexRAG backend running"}