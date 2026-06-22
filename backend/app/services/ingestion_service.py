import tiktoken
import pdfplumber
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.embedding_model import embedding_model
from app.services.hierarchy_parser import parse_pages
from app.db import documents_collection, chunks_collection

#Text Extraction
# Extraction returns per-line font metadata so the hierarchy parser can detect
# headings: [{"lines": [{"text", "size", "bold"}], "page": int | None}].


def extract_text_from_pdf(file_path: str) -> list[dict]:
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text_lines = page.extract_text_lines(return_chars=True)
            lines = []
            for tl in text_lines:
                text = (tl.get("text") or "").strip()
                if not text:
                    continue
                chars = tl.get("chars") or []
                sizes = [c["size"] for c in chars if c.get("size")]
                size = max(sizes) if sizes else None
                bold = any("bold" in (c.get("fontname") or "").lower() for c in chars)
                lines.append({"text": text, "size": size, "bold": bold})
            if lines:
                pages.append({"lines": lines, "page": i + 1})
    return pages


def extract_text_from_docx(file_path: str) -> list[dict]:
    doc = DocxDocument(file_path)
    lines = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        # DOCX has no reliable point size here; flag bold if any run is bold.
        bold = any(run.bold or (run.font and run.font.bold) for run in p.runs)
        lines.append({"text": text, "size": None, "bold": bold})
    return [{"lines": lines, "page": None}]

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

def chunk_blocks(blocks: list[dict]) -> list[dict]:
    # Chunk each hierarchy block separately so a chunk never straddles two
    # sections, and propagate the block's hierarchy tags onto every chunk.
    all_chunks = []
    for block in blocks:
        text_chunks = splitter.split_text(block["text"])
        for chunk_text in text_chunks:
            all_chunks.append({
                "text": chunk_text,
                "page": block["page"],
                "section": block["section"],
                "clause": block["clause"],
                "subclause": block["subclause"],
            })
    return all_chunks

# Embedding and database storage


def ingest_document(file_path: str, filename: str, file_type: str):
    if file_type == "pdf":
        pages = extract_text_from_pdf(file_path)
    elif file_type == "docx":
        pages = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    if not pages:
        raise ValueError("No text could be extracted from this document")

    blocks = parse_pages(pages)
    chunks = chunk_blocks(blocks)

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
            "embedding": embedding.tolist(),
            "section": chunk["section"],
            "clause": chunk["clause"],
            "subclause": chunk["subclause"]
        })

    chunks_collection.insert_many(chunk_records)

    return {
        "document_id": str(document_id),
        "filename": filename,
        "pages_extracted": len(pages),
        "chunks_created": len(chunks)
    }
