import tiktoken
import pdfplumber
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

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