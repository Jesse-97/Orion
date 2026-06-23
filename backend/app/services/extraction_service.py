import re

from app.models.reranker_model import reranker_model

TOP_SENTENCES_PER_CHUNK = 2
NEIGHBOUR_WINDOW = 1
MIN_SENTENCES_TO_EXTRACT = 4  # below this, return chunk unchanged

# Split on ". ", "? ", "! " (the whitespace itself is consumed) only when the
# next sentence begins with an uppercase letter. The lookbehind keeps the
# terminal punctuation attached to the preceding sentence, and the uppercase
# lookahead avoids splitting decimals / lowercase abbreviations.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.?!])\s+(?=[A-Z])")


def _split_sentences(text: str) -> list[str]:
    return _SENTENCE_BOUNDARY.split(text.strip())


def extract(query: str, chunks: list[dict]) -> list[dict]:
    """Replace each chunk's text with a query-focused extract.

    For every chunk we score its individual sentences against the query, keep
    the top-scoring ones, expand each by a neighbour window for context, then
    reassemble the kept sentences in their original order. Chunks too short to
    extract from are returned unchanged. All non-text fields are preserved.
    """
    extracted = []
    for chunk in chunks:
        sentences = _split_sentences(chunk["text"])

        # One early-return covers every small-chunk edge case: a single
        # unsplittable run-on, fewer sentences than we'd pick, or simply a
        # chunk too short to be worth extracting from.
        if len(sentences) < MIN_SENTENCES_TO_EXTRACT:
            extracted.append(chunk)
            continue

        # Score all sentences against the query in one batched reranker call.
        scores = reranker_model.score(query, sentences)

        # Top-N sentence indices by score.
        ranked = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)
        picked = ranked[:TOP_SENTENCES_PER_CHUNK]

        # Expand each picked index by +/- NEIGHBOUR_WINDOW; the set dedupes overlaps.
        keep = set()
        for idx in picked:
            for j in range(idx - NEIGHBOUR_WINDOW, idx + NEIGHBOUR_WINDOW + 1):
                if 0 <= j < len(sentences):
                    keep.add(j)

        # Reassemble in original position order (NOT by score).
        ordered_indices = sorted(keep)
        extracted_text = " ".join(sentences[j] for j in ordered_indices)

        extracted.append({**chunk, "text": extracted_text})

    return extracted
