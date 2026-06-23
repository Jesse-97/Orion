# Ollama implementation of the synthesis service.
#
# Synthesis runs against a LOCAL Ollama instance (gemma3:4b on
# http://localhost:11434) instead of the Gemini API, because the Gemini key is
# blocked by a Google account-level restriction. Everything else — the function
# signature synthesize(query, top_chunks), the return schema, the threshold
# gate, the system prompt, the fence-stripping fallback and the graceful error
# handling — is unchanged from the Gemini version.
#
# Swapping back to Gemini is a single-function change: only the API call inside
# synthesize() needs to be restored (re-add the genai client + generate_content
# call); the rest of this module is provider-agnostic.

import json

import requests

# Top rerank score below this -> skip the API call and report insufficient evidence.
# Chosen from observed reranker scores (relevant ~ -0.71, irrelevant ~ -5.77 / -6.69).
RELEVANCE_THRESHOLD = -5.0

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"

SYSTEM_PROMPT = """You are a legal document analysis assistant.

Answer the user's question using ONLY the provided context passages. Never use
general knowledge or information outside the context. If the answer cannot be found
in the context, say so.

Respond with a single JSON object matching EXACTLY this schema:
{
  "answer": str,
  "citation": {
    "document": str,
    "section": str | null,
    "clause": str | null,
    "page": int | null
  },
  "confidence": "high" | "medium" | "low",
  "reasoning": str
}

Rules:
- "answer" is a direct, concise answer grounded in the context.
- "citation" must point to the single passage that best supports the answer, using
  its document filename, section, clause and page. Use null for any field that the
  supporting passage does not have.
- "confidence" reflects how directly the context supports the answer.
- "reasoning" briefly explains which passage(s) the answer came from.
- If the answer is NOT in the provided context, set "answer" to
  "Not found in provided documents", set "citation" to null, and set
  "confidence" to "low".
"""


def _format_context(top_chunks):
    blocks = []
    for i, chunk in enumerate(top_chunks, start=1):
        blocks.append(
            f"[Passage {i}]\n"
            f"document: {chunk.get('filename')}\n"
            f"page: {chunk.get('page')}\n"
            f"section: {chunk.get('section')}\n"
            f"clause: {chunk.get('clause')}\n"
            f"subclause: {chunk.get('subclause')}\n"
            f"text: {chunk.get('text')}"
        )
    return "\n\n".join(blocks)


def _parse_response(raw_text):
    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        # Fallback: strip markdown code fences if present, then retry.
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
            cleaned = cleaned.removeprefix("json").strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[: -len("```")].strip()
        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            return {
                "answer": "Failed to parse model response",
                "citation": None,
                "confidence": "low",
                "reasoning": "The synthesis model did not return valid JSON",
            }


def synthesize(query: str, top_chunks: list) -> dict:
    if not top_chunks or top_chunks[0].get("relevance_score", float("-inf")) < RELEVANCE_THRESHOLD:
        return {
            "answer": "Insufficient evidence found in the provided documents",
            "citation": None,
            "confidence": "low",
            "reasoning": "No sufficiently relevant chunks found",
        }

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Context passages:\n{_format_context(top_chunks)}\n\n"
        f"Question: {query}"
    )

    try:
        # "format": "json" enforces JSON output natively on Ollama, the local
        # equivalent of Gemini's response_mime_type="application/json". The
        # fence-stripping fallback in _parse_response is just defensive.
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        raw = response.json()["response"]
    except Exception as exc:
        return {
            "answer": "Synthesis temporarily unavailable",
            "citation": None,
            "confidence": "low",
            "reasoning": f"Ollama API call failed: {exc}",
        }

    return _parse_response(raw)
