"""Concept dependency helpers for prerequisite-aware analytics."""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.ai import ConceptExtractionItem
from app.utils.text import slugify


LINEAR_ALGEBRA_CHAIN = [
    "matrix-multiplication",
    "determinant",
    "eigenvalues",
    "eigenvectors",
]

LINEAR_ALGEBRA_NAMES = {
    "matrix-multiplication": "Matrix Multiplication",
    "determinant": "Determinant",
    "eigenvalues": "Eigenvalues",
    "eigenvectors": "Eigenvectors",
}

LINEAR_ALGEBRA_DESCRIPTIONS = {
    "matrix-multiplication": "How matrices combine to form new linear transformations.",
    "determinant": "How a matrix scales space and whether it is invertible.",
    "eigenvalues": "Scaling factors tied to special directions of a transformation.",
    "eigenvectors": "Directions that keep their orientation under transformation.",
}


@dataclass
class ConceptSeed:
    name: str
    slug: str
    description: str | None
    is_inferred: bool = False
    prerequisite_slug: str | None = None


def enrich_with_prerequisites(concepts: list[ConceptExtractionItem]) -> list[ConceptSeed]:
    extracted_by_slug = {slugify(concept.slug or concept.name): concept for concept in concepts}
    present_chain: set[str] = set()

    for slug in LINEAR_ALGEBRA_CHAIN:
        concept = extracted_by_slug.get(slug)
        if concept:
            present_chain.add(slug)
            index = LINEAR_ALGEBRA_CHAIN.index(slug)
            present_chain.update(LINEAR_ALGEBRA_CHAIN[: index + 1])

    ordered: list[ConceptSeed] = []
    seen: set[str] = set()

    for slug in LINEAR_ALGEBRA_CHAIN:
        if slug not in present_chain or slug in seen:
            continue
        extracted = extracted_by_slug.get(slug)
        ordered.append(
            ConceptSeed(
                name=extracted.name if extracted else LINEAR_ALGEBRA_NAMES[slug],
                slug=slug,
                description=(extracted.description if extracted else LINEAR_ALGEBRA_DESCRIPTIONS[slug]),
                is_inferred=extracted is None,
                prerequisite_slug=_previous_slug(slug),
            )
        )
        seen.add(slug)

    for concept in concepts:
        slug = slugify(concept.slug or concept.name)
        if slug in seen:
            continue
        ordered.append(
            ConceptSeed(
                name=concept.name,
                slug=slug,
                description=concept.description,
                is_inferred=False,
            )
        )
        seen.add(slug)

    if not ordered:
        return [
            ConceptSeed(name=concept.name, slug=slugify(concept.slug or concept.name), description=concept.description)
            for concept in concepts
        ]
    return ordered


def _previous_slug(slug: str) -> str | None:
    try:
        index = LINEAR_ALGEBRA_CHAIN.index(slug)
    except ValueError:
        return None
    if index == 0:
        return None
    return LINEAR_ALGEBRA_CHAIN[index - 1]
