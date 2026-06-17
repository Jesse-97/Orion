import faiss
import numpy as np
from app.db import chunks_collection

def build_faiss_index():
    """
    Loads all chunk embeddings from MongoDB into a FAISS index.
    Returns (index, chunk_records) — chunk_records preserves order
    matching the index's internal IDs.
    """
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