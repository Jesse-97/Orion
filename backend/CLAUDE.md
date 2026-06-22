# LexRAG — Legal Document Intelligence System

## Project Context
RAG-based legal document Q&A system. Phase 1 (basic RAG pipeline) is complete.
Currently implementing Phase 2: hierarchy-preserving chunking.

## Stack
- Python 3.14, FastAPI, MongoDB (Docker), FAISS, BGE embeddings, MiniLM reranker
- Gemini API (free tier) for synthesis — NOT Claude/Anthropic API
- pdfplumber for PDF extraction, python-docx for DOCX

## Architecture
- app/models/ — BGE singleton (embed_chunk/embed_query), MiniLM singleton
- app/services/ingestion_service.py — extraction, chunking, ingestion pipeline
- app/services/retrieval_service.py — FAISS index, search pipeline
- app/routes/ — FastAPI upload and query routes
- app/db.py — MongoDB collections (documents, chunks)

## Critical Rules
- BGE query prefix MUST only be in embed_query(), never embed_chunk()
- Chunking uses RecursiveCharacterTextSplitter, chunk_size=300, overlap=50
- Embeddings stored as .tolist() in MongoDB, converted back to float32 for FAISS
- Never modify the singleton pattern in embedding_model.py or reranker_model.py
- Do not add new dependencies without checking disk quota first (run df -h)

## Phase 2 Goal
Add hierarchy-preserving chunking:
- Parse Section → Clause → Sub-clause structure from PDF/DOCX using regex
- Tag every chunk with section, clause, subclause, page metadata
- Store this metadata in MongoDB alongside existing chunk fields
- Do NOT break existing ingestion pipeline — hierarchy metadata is additive

## Current MongoDB Chunk Schema
{
  document_id, filename, text, page, embedding
}

## Target Chunk Schema After Phase 2
{
  document_id, filename, text, page, embedding,
  section, clause, subclause   ← new fields, None if not detected
}