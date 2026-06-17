import tiktoken
import pdfplumber
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.embedding_model import embedding_model
from app.db import documents_collection, chunks_collection

#Text Extraction

def extract_text_from_pdf(file_path: str) -> list[dict]:
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "text": text.strip(),
                    "page": i + 1
                })
    return pages


def extract_text_from_docx(file_path: str) -> list[dict]:
    doc = DocxDocument(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full_text = "\n\n".join(paragraphs)
    return [{"text": full_text, "page": None}]

#Tokenization and chunking

tokenizer = tiktoken.get_encoding("cl100k_base")

def token_length(text: str) -> int:
    return len(tokenizer.encode(text))

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    length_function=token_length,
    separators=["\n\n", "\n", ". ", " ", ""]
)

def chunk_pages(pages: list[dict]) -> list[dict]:
    all_chunks = []
    for page_data in pages:
        text_chunks = splitter.split_text(page_data["text"])
        for chunk_text in text_chunks:
            all_chunks.append({
                "text": chunk_text,
                "page": page_data["page"]
            })
    return all_chunks

#Embedding and database storage


def ingest_document(file_path: str, filename: str, file_type: str):
    if file_type == "pdf":
        pages = extract_text_from_pdf(file_path)
    elif file_type == "docx":
        pages = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    if not pages:
        raise ValueError("No text could be extracted from this document")

    chunks = chunk_pages(pages)

    # Document metadata storage
    doc_record = documents_collection.insert_one({
        "filename": filename,
        "file_type": file_type,
        "page_count": len(pages),
        "chunk_count": len(chunks)
    })
    document_id = doc_record.inserted_id

    # Embedding and chunk storage
    chunk_records = []
    for chunk in chunks:
        embedding = embedding_model.embed_chunk(chunk["text"])
        chunk_records.append({
            "document_id": document_id,
            "filename": filename,
            "text": chunk["text"],
            "page": chunk["page"],
            "embedding": embedding.tolist()
        })

    chunks_collection.insert_many(chunk_records)

    return {
        "document_id": str(document_id),
        "filename": filename,
        "pages_extracted": len(pages),
        "chunks_created": len(chunks)
    }
