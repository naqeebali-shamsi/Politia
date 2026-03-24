import logging
import re

logger = logging.getLogger(__name__)

# Titles to strip before matching
TITLES = re.compile(
    r"^(Shri|Smt\.?|Dr\.?|Prof\.?|Adv\.?|Er\.?|Mrs\.?|Ms\.?|Mr\.?)\s*",
    re.IGNORECASE,
)


def normalize_name(name: str) -> str:
    """Normalize an Indian politician name for matching."""
    name = name.strip()
    # Loop to strip stacked titles: "Shri Dr. Rajesh Kumar" -> "Rajesh Kumar"
    while True:
        stripped = TITLES.sub("", name).strip()
        if stripped == name:
            break
        name = stripped
    name = re.sub(r"\s+", " ", name)
    name = name.strip().upper()
    return name


def match_names(name_a: str, name_b: str) -> float:
    """
    Fuzzy match two names and return a similarity score (0-100).
    Falls back to simple comparison if rapidfuzz is not installed.
    """
    a = normalize_name(name_a)
    b = normalize_name(name_b)

    if a == b:
        return 100.0

    try:
        from rapidfuzz import fuzz
        # Use token_sort_ratio for name reordering ("Modi Narendra" vs "Narendra Modi")
        return fuzz.token_sort_ratio(a, b)
    except ImportError:
        # Simple fallback: character overlap
        if not a or not b:
            return 0.0
        common = set(a.split()) & set(b.split())
        total = set(a.split()) | set(b.split())
        return (len(common) / len(total) * 100) if total else 0.0


def find_best_match(
    name: str,
    candidates: list[dict],
    name_key: str = "full_name",
    threshold: float = 80.0,
) -> dict | None:
    """
    Find the best matching candidate from a list.
    Returns the best match dict or None if no match above threshold.
    """
    best_score = 0.0
    best_match = None

    for candidate in candidates:
        candidate_name = candidate.get(name_key, "")
        score = match_names(name, candidate_name)
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_score >= threshold:
        logger.debug(f"Matched '{name}' -> '{best_match.get(name_key)}' (score={best_score:.1f})")
        return best_match

    return None
