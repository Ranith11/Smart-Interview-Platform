"""
SmartInterview — Bloom's Taxonomy Module (Week 8)

Defines six cognitive levels used by the adaptive learning engine
to control question complexity progression.

Levels:
    1. Remember   — Recall facts, definitions, terminology
    2. Understand  — Explain concepts, summarize, interpret
    3. Apply       — Use knowledge in practical situations
    4. Analyze     — Compare, break down, identify relationships
    5. Evaluate    — Judge, justify decisions, critique solutions
    6. Create      — Design, propose, architect new solutions
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BloomLevel:
    """Immutable representation of a single Bloom Taxonomy level."""
    id: str
    name: str
    order: int
    description: str
    question_guidance: str


# ── Six Bloom Levels ──────────────────────────────────────────

REMEMBER = BloomLevel(
    id="remember",
    name="Remember",
    order=1,
    description="Recall facts, definitions, and basic terminology.",
    question_guidance=(
        "Ask the candidate to recall or define a specific concept, term, or fact. "
        "The answer should demonstrate basic knowledge retrieval. "
        "Example verbs: define, list, name, identify, state."
    ),
)

UNDERSTAND = BloomLevel(
    id="understand",
    name="Understand",
    order=2,
    description="Explain concepts, summarize ideas, interpret meaning.",
    question_guidance=(
        "Ask the candidate to explain a concept in their own words, summarize how "
        "something works, or interpret the purpose of a technique. "
        "Example verbs: explain, describe, summarize, interpret, illustrate."
    ),
)

APPLY = BloomLevel(
    id="apply",
    name="Apply",
    order=3,
    description="Use knowledge to solve problems in practical situations.",
    question_guidance=(
        "Ask the candidate to apply their knowledge to solve a specific problem, "
        "implement a solution, or use a concept in a given scenario. "
        "Example verbs: implement, use, solve, demonstrate, apply."
    ),
)

ANALYZE = BloomLevel(
    id="analyze",
    name="Analyze",
    order=4,
    description="Compare approaches, break down problems, identify relationships.",
    question_guidance=(
        "Ask the candidate to compare two or more approaches, break down a complex "
        "problem into components, or identify relationships between concepts. "
        "Example verbs: compare, contrast, differentiate, examine, break down."
    ),
)

EVALUATE = BloomLevel(
    id="evaluate",
    name="Evaluate",
    order=5,
    description="Judge solutions, justify decisions, critique approaches.",
    question_guidance=(
        "Ask the candidate to evaluate a proposed solution, justify a technical "
        "decision, or critique an approach with supporting reasoning. "
        "Example verbs: evaluate, justify, argue, critique, assess."
    ),
)

CREATE = BloomLevel(
    id="create",
    name="Create",
    order=6,
    description="Design new solutions, propose architectures, synthesize ideas.",
    question_guidance=(
        "Ask the candidate to design a solution, propose an architecture, or "
        "create a new approach that synthesizes multiple concepts. "
        "Example verbs: design, propose, create, formulate, construct."
    ),
)


# ── Ordered registry ──────────────────────────────────────────

ALL_LEVELS: list[BloomLevel] = [REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE]

_BY_ID: dict[str, BloomLevel] = {level.id: level for level in ALL_LEVELS}
_BY_ORDER: dict[int, BloomLevel] = {level.order: level for level in ALL_LEVELS}

MIN_ORDER = 1   # Remember
MAX_ORDER = 6   # Create


# ── Public helpers ────────────────────────────────────────────

def get_bloom_level(identifier) -> BloomLevel:
    """
    Get a BloomLevel by its string id ('remember') or numeric order (1).
    Raises ValueError if not found.
    """
    if isinstance(identifier, int):
        if identifier in _BY_ORDER:
            return _BY_ORDER[identifier]
        raise ValueError(f"Invalid Bloom order: {identifier}. Must be {MIN_ORDER}–{MAX_ORDER}.")
    if isinstance(identifier, str):
        key = identifier.lower().strip()
        if key in _BY_ID:
            return _BY_ID[key]
        raise ValueError(f"Invalid Bloom id: '{identifier}'. Valid: {list(_BY_ID.keys())}")
    raise TypeError(f"Expected int or str, got {type(identifier)}")


def next_level(current: BloomLevel) -> BloomLevel | None:
    """
    Return the next higher Bloom level, or None if already at Create (max).
    Never exceeds Create.
    """
    next_order = current.order + 1
    if next_order > MAX_ORDER:
        return None
    return _BY_ORDER[next_order]


def prev_level(current: BloomLevel) -> BloomLevel | None:
    """
    Return the next lower Bloom level, or None if already at Remember (min).
    Never goes below Remember.
    """
    prev_order = current.order - 1
    if prev_order < MIN_ORDER:
        return None
    return _BY_ORDER[prev_order]


def clamp_bloom_order(order: int) -> int:
    """Clamp a Bloom order to valid bounds [1, 6]."""
    return max(MIN_ORDER, min(MAX_ORDER, order))
