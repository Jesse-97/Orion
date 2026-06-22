import json

from google import genai

from app.config import GEMINI_API_KEY

# Top rerank score below this -> skip the API call and report insufficient evidence.
# Chosen from observed reranker scores (relevant ~ -0.71, irrelevant ~ -5.77 / -6.69).
RELEVANCE_THRESHOLD = -5.0

client = genai.Client(api_key=GEMINI_API_KEY)

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
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
    except Exception as exc:
        return {
            "answer": "Synthesis temporarily unavailable",
            "citation": None,
            "confidence": "low",
            "reasoning": f"Gemini API call failed: {exc}",
        }

    return _parse_response(response.text)
