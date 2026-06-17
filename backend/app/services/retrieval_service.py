import faiss
import numpy as np
from app.db import chunks_collection
from app.models.embedding_model import embedding_model
from app.models.reranker_model import reranker_model

def build_faiss_index():
    all_chunks = list(chunks_collection.find({}))

    if not all_chunks:
        return None, []

    embeddings = np.array(
        [chunk["embedding"] for chunk in all_chunks]
    ).astype("float32")

    dimension = embeddings.shape[1]  
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index, all_chunks

def search(query: str, top_k_retrieve: int = 10, top_k_rerank: int = 3):
    index, all_chunks = build_faiss_index()
    if index is None:
        return []

    # Ebedding query WITH prefix
    query_vector = embedding_model.embed_query(query).astype("float32").reshape(1, -1)

    # Cosine similarity search in FAISS
    actual_k = min(top_k_retrieve, index.ntotal)
    similarity_scores, indices = index.search(query_vector, actual_k)
    candidates = [all_chunks[i] for i in indices[0]]

    # Reranking
    passages = [c["text"] for c in candidates]
    rerank_scores = reranker_model.score(query, passages)

    # Taking top_k_rerank results
    ranked = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)
    top_results = ranked[:top_k_rerank]

    return [
        {
            "text": chunk["text"],
            "filename": chunk["filename"],
            "page": chunk["page"],
            "relevance_score": float(score)
        }
        for chunk, score in top_results
    ]