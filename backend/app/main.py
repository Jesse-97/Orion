from fastapi import FastAPI
from app.routes import upload_routes, query_routes

app = FastAPI(title="LexRAG", description="Legal Document Intelligence System")

app.include_router(upload_routes.router, prefix="/api")
app.include_router(query_routes.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "LexRAG backend running"}