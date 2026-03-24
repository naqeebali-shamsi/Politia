import logging
import re

logger = logging.getLogger(__name__)

# Titles to strip before matching — word boundary \b prevents matching SHRIMAN as SHRI+MAN
TITLES = re.compile(
    r"^(Shri|Smt\.?|Dr\.?|Prof\.?|Adv\.?|Er\.?|Mrs\.?|Ms\.?|Mr\.?)\b\.?\s*",
    re.IGNORECASE,
)

# Common Indian names that appear dozens of times across constituencies.
# These require strict constituency+state match to avoid over-merging.
_COMMON_NAME_TOKENS = {
    "KUMAR", "SINGH", "RAM", "LAL", "PRASAD", "CHAND", "DAS",
    "PRAKASH", "NATH", "DEVI", "BAI",
}

_COMMON_FULL_NAMES = {
    "OM PRAKASH", "ASHOK KUMAR", "RAM KUMAR", "RAJESH KUMAR", "VIJAY KUMAR",
    "MAHESH KUMAR", "NARENDRA SINGH", "KARAM SINGH", "RAJ KUMAR",
    "RAM LAL", "SANTOSH SINGH", "RAJESH SINGH", "SURESH KUMAR",
    "ASHWANI KUMAR", "RAJEEV KUMAR", "LAL BAHADUR SINGH",
    "RAM PRASAD", "SANT KUMAR", "HARCHARAN SINGH", "BALESHWAR RAM",
}

# Legacy state name → modern state name mapping
_STATE_MAP = {
    "BOMBAY": "MAHARASHTRA",
    "MADRAS": "TAMIL NADU",
    "MYSORE": "KARNATAKA",
    "HYDERABAD": "ANDHRA PRADESH",
    "TRAVANCORE-COCHIN": "KERALA",
    "PATIALA AND EAST PUNJAB STATES UNION": "PUNJAB",
    "PEPSU": "PUNJAB",
    "BHOPAL": "MADHYA PRADESH",
    "VINDHYA PRADESH": "MADHYA PRADESH",
    "MADHYA BHARAT": "MADHYA PRADESH",
    "SAURASHTRA": "GUJARAT",
    "KUTCH": "GUJARAT",
    "AJMER": "RAJASTHAN",
    "COORG": "KARNATAKA",
    "BILASPUR": "HIMACHAL PRADESH",
}


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


# ============================================================================
# P0-3: New entity resolution functions
# ============================================================================

def clean_name_for_storage(name: str) -> str:
    """
    Strip all honorific titles from a name for clean DB storage.
    Unlike normalize_name(), this does NOT uppercase — preserves original case.
    """
    result = name.strip()
    while True:
        stripped = TITLES.sub("", result).strip()
        if stripped == result:
            break
        result = stripped
    result = re.sub(r"\s+", " ", result).strip()
    return result.upper() if result else result


def normalize_state(state: str) -> str:
    """Map legacy Indian state names to modern equivalents."""
    s = state.strip().upper()
    return _STATE_MAP.get(s, s)


def is_common_name(name: str) -> bool:
    """
    Check if a name is common enough to require strict constituency matching.
    Common names like OM PRAKASH, ASHOK KUMAR appear dozens of times
    across different constituencies and must not be over-merged.
    """
    norm = normalize_name(name)

    # Direct match against known common full names
    if norm in _COMMON_FULL_NAMES:
        return True

    # Check if name is composed entirely of common tokens
    tokens = set(norm.split())
    if len(tokens) <= 2 and tokens.issubset(_COMMON_NAME_TOKENS):
        return True

    return False


def is_temporally_plausible(last_election_year: int, disclosure_year: int) -> bool:
    """
    Check if a disclosure record is temporally plausible for a politician.
    A 2014 affidavit should not match to a politician last seen in 1960.
    Max gap: 10 years (allows one election cycle gap).
    """
    gap = disclosure_year - last_election_year
    return gap <= 10


def should_merge(record_a: dict, record_b: dict) -> bool:
    """
    Determine whether two candidate records refer to the same person.
    Uses name similarity, constituency, state, and name commonality
    to prevent over-merging of common names while allowing
    legitimate cross-constituency matches for distinctive names.
    """
    name_a = normalize_name(record_a.get("name", ""))
    name_b = normalize_name(record_b.get("name", ""))

    if not name_a or not name_b:
        return False

    name_score = match_names(record_a.get("name", ""), record_b.get("name", ""))

    const_a = (record_a.get("constituency") or "").upper()
    const_b = (record_b.get("constituency") or "").upper()
    state_a = normalize_state(record_a.get("state") or "")
    state_b = normalize_state(record_b.get("state") or "")
    year_a = record_a.get("year", 0)
    year_b = record_b.get("year", 0)

    # Same name, same constituency → always merge
    if name_score >= 85.0 and const_a == const_b:
        return True

    # Different state → never merge (even if name matches perfectly)
    if state_a != state_b:
        return False

    # Same year, different constituency → different people
    if year_a == year_b and const_a != const_b:
        return False

    # Common names need exact constituency match
    if is_common_name(record_a.get("name", "")):
        return name_score >= 90.0 and const_a == const_b

    # Uncommon names: allow cross-constituency merge within same state
    # if name match is strong (handles constituency changes like Sonia Gandhi)
    if name_score >= 90.0:
        return True

    return False
