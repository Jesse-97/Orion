# test_phase2.py
from app.db import documents_collection, chunks_collection
from app.services.ingestion_service import ingest_document

FILENAME = "sample.pdf"
FILE_PATH = "/home/brooke/Documents/sample.pdf"

documents_collection.delete_many({"filename": FILENAME})
chunks_collection.delete_many({"filename": FILENAME})

result = ingest_document(FILE_PATH, FILENAME, "pdf")
print(result)

# Check hierarchy metadata is present
sample = chunks_collection.find_one({"filename": FILENAME})
print(f"text: {sample['text'][:100]}")
print(f"page: {sample['page']}")
print(f"section: {sample['section']}")
print(f"clause: {sample['clause']}")
print(f"subclause: {sample['subclause']}")
print(f"embedding length: {len(sample['embedding'])}")

# Check how many chunks got hierarchy tags vs None
total = chunks_collection.count_documents({"filename": FILENAME})
with_section = chunks_collection.count_documents({"filename": FILENAME, "section": {"$ne": None}})
with_clause = chunks_collection.count_documents({"filename": FILENAME, "clause": {"$ne": None}})
print(f"\nTotal chunks: {total}")
print(f"Chunks with section tag: {with_section}")
print(f"Chunks with clause tag: {with_clause}")