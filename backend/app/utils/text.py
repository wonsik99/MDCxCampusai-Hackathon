"""Text normalization and fallback concept heuristics."""

from __future__ import annotations

import re
from collections import Counter


STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "this",
    "from",
    "into",
    "your",
    "about",
    "have",
    "will",
    "each",
    "their",
    "then",
    "when",
    "where",
    "which",
    "what",
    "been",
    "being",
    "lecture",
    "concept",
    "student",
}


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "concept"


def clean_lecture_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned.strip()


def summarize_text_fallback(text: str, limit: int = 420) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentences[:3]).strip()
    if not summary:
        summary = text[:limit]
    return summary[:limit].strip()


def extract_keyword_concepts(text: str, max_items: int = 4) -> list[dict[str, str]]:
    lowered = text.lower()
    canonical_candidates = [
        ("matrix multiplication", "Combining matrices while respecting row-by-column structure."),
        ("determinant", "A scalar summary of how a matrix scales and transforms space."),
        ("eigenvalues", "Values that describe how a matrix stretches special directions."),
        ("eigenvectors", "Directions that remain aligned after a matrix transformation."),
    ]
    concepts: list[dict[str, str]] = []
    for name, description in canonical_candidates:
        if name in lowered:
            concepts.append({"name": name.title(), "slug": slugify(name), "description": description})

    words = re.findall(r"[a-zA-Z]{5,}", text.lower())
    counts = Counter(word for word in words if word not in STOPWORDS)
    for word, _ in counts.most_common(max_items * 3):
        pretty = word.replace("-", " ").title()
        slug = slugify(word)
        if any(item["slug"] == slug for item in concepts):
            continue
        concepts.append(
            {
                "name": pretty,
                "slug": slug,
                "description": f"Key idea from the lecture related to {pretty.lower()}.",
            }
        )
        if len(concepts) >= max_items:
            break
    return concepts[:max_items] or [{"name": "Core Idea", "slug": "core-idea", "description": "Primary concept in the lecture."}]
