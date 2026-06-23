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

## Phase 3 Goal
Add Gemini API synthesis with structured JSON citation output.

- Install: google-generativeai (check disk first with df -h)
- New file: app/services/synthesis_service.py
  - Gemini 2.0 Flash model
  - Structured JSON output (response_mime_type application/json)
  - Returns: {answer, citation: {document, section, clause, page}, confidence, reasoning}
  - If top rerank score below -8.0 threshold → return "Insufficient evidence" without API call
- Modify: app/services/retrieval_service.py
  - search() currently returns raw chunks
  - Add synthesis call after reranking: pass top chunks + their metadata to synthesis_service
  - Return structured citation response instead of raw chunks
- Modify: app/routes/query_routes.py
  - Response now returns structured citation JSON not just results list
- Do NOT modify embedding_model.py, reranker_model.py, hierarchy_parser.py, 
  ingestion_service.py, or db.py
- GEMINI_API_KEY already in .env

## Phase 3.5 — Frontend (React + Vite)

Goal: clean, demoable dark-theme UI for LexRAG. NOT a fancy production UI — 
a polished portfolio frontend that shows the system off well.

Location: lexrag/frontend/ (sibling to backend/)
Stack: React 18, Vite, Axios, Tailwind CSS, Framer Motion (animations)

Pages needed:
1. Upload screen — drag-and-drop or file picker for PDF/DOCX
2. Query screen — text input, displays structured citation response

Key UI requirements:
- Dark theme: deep neutrals (zinc/slate), single accent color (cyan or violet)
- The citation block must be visually distinct — section/clause/page shown 
  as styled "chips" or badges, not buried in text
- Confidence indicator: color-coded (high=green, medium=amber, low=red)
- Loading states: skeleton or spinner during upload and query
- Smooth fade/slide transitions when answers appear (Framer Motion)
- Typography: system font stack, larger text for the answer, smaller for citation
- Responsive: works on mobile and desktop

Backend API (already running on http://localhost:8000):
- POST /api/upload — multipart file upload, returns {document_id, filename, 
  pages_extracted, chunks_created}
- POST /api/query — JSON body {question}, returns {query, response: {answer, 
  citation: {document, section, clause, page}, confidence, reasoning}}

CORS: backend may need fastapi.middleware.cors configured to allow Vite dev 
server origin (http://localhost:5173). Add to app/main.py if not present.

Do NOT modify any backend files except adding CORS middleware to main.py.


## Phase 4 — Sentence-Level Extraction with Neighbour Expansion

Goal: trim each top chunk down to its most relevant sentences before 
sending to the LLM, while preserving semantic context via neighbour expansion.

Pipeline change:
  Before: top 3 reranked chunks → full text → LLM
  After:  top 3 reranked chunks → split into sentences → 
          cross-encoder scores each sentence vs query → 
          pick top N sentences per chunk → expand to include 
          neighbour sentence on each side → 
          dedupe and reorder by original position → 
          concatenated extracted text → LLM

Critical rules:
- REUSE existing reranker_model singleton — do NOT load a second model
- Configurable params: TOP_SENTENCES_PER_CHUNK = 2, NEIGHBOUR_WINDOW = 1
- Preserve original sentence order in the output (do not sort by score)
- Dedupe: if sentence_3 is picked AND sentence_4 is picked, their 
  neighbour expansions overlap — dedupe by index before reassembling
- The chunk's hierarchy metadata (section/clause/subclause/page) 
  remains attached to the extracted text, not the individual sentences
- Sentence splitting: use simple regex on ". " / "? " / "! " followed 
  by capital letter — keep simple, no external NLP library

Where it slots in:
- New file: app/services/extraction_service.py
- Modify: app/services/retrieval_service.py — after rerank, call 
  extraction_service.extract(query, top_chunks) before passing to 
  synthesis_service.synthesize()
- Keep synthesize=False path returning raw chunks (no extraction) for 
  debugging

Do NOT modify: embedding_model.py, reranker_model.py (only call its 
score() method), hierarchy_parser.py, ingestion_service.py, db.py, 
synthesis_service.py, any frontend file.