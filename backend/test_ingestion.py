from app.services.ingestion_service import ingest_document
from app.db import documents_collection, chunks_collection

FILE_PATH = "/home/brooke/Documents/sample.pdf"
FILENAME = "sample.pdf"  

documents_collection.delete_many({"filename": FILENAME})
chunks_collection.delete_many({"filename": FILENAME})

result = ingest_document(FILE_PATH, FILENAME, "pdf")
print(result)

chunk_count = chunks_collection.count_documents({"filename": FILENAME})
print(f"Chunks found in MongoDB: {chunk_count}")

sample_chunk = chunks_collection.find_one({"filename": FILENAME})
print(f"Sample chunk text: {sample_chunk['text'][:150]}")
print(f"Embedding type: {type(sample_chunk['embedding'])}")
print(f"Embedding length: {len(sample_chunk['embedding'])}")