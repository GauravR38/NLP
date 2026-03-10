from typing import List, Tuple


STRONG_VERBS = [
    "accelerated",
    "achieved",
    "administered",
    "automated",
    "built",
    "conducted",
    "coordinated",
    "designed",
    "developed",
    "enhanced",
    "executed",
    "implemented",
    "improved",
    "launched",
    "led",
    "optimized",
    "reduced",
    "streamlined",
    "spearheaded",
    "transformed",
]

WEAK_VERBS = [
    "helped",
    "worked on",
    "worked with",
    "assisted",
    "participated in",
    "involved in",
    "responsible for",
    "did",
    "made",
    "handled",
]


def split_into_bullets(text: str) -> List[str]:
    """
    Split resume text into bullet-like sentences.
    This is a heuristic split on newlines and periods.
    """
    raw_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Remove leading bullet characters
        for bullet in ("- ", "* ", "• "):
            if line.startswith(bullet):
                line = line[len(bullet) :]
                break
        raw_lines.append(line)

    bullets: List[str] = []
    for line in raw_lines:
        # Further split on periods if lines are long
        segments = [seg.strip() for seg in line.split(".") if seg.strip()]
        bullets.extend(segments)

    return bullets


def improve_bullet(bullet: str) -> str:
    """
    Improve a single resume bullet using stronger verbs and clearer phrasing.
    """
    original = bullet.strip()
    lowered = original.lower()

    # Replace weak verbs at start
    for weak in WEAK_VERBS:
        if lowered.startswith(weak):
            # map to a strong verb heuristically
            strong = STRONG_VERBS[0]
            rest = original[len(weak) :].lstrip(" -:,.")
            if not rest:
                return original
            return strong.capitalize() + " " + rest

    # If bullet already starts with a strong verb, just ensure it is capitalized and concise
    for strong in STRONG_VERBS:
        if lowered.startswith(strong):
            return strong.capitalize() + original[len(strong) :]

    # Default: prepend a strong verb if bullet looks like a noun phrase
    # Example: "data pipelines for analytics" -> "Developed data pipelines for analytics"
    if " " in original:
        return STRONG_VERBS[2].capitalize() + " " + original
    return original


def generate_rewrite_suggestions(
    resume_text: str, max_bullets: int = 10
) -> List[Tuple[str, str]]:
    """
    Generate (original, improved) bullet point suggestions.
    """
    bullets = split_into_bullets(resume_text)
    suggestions: List[Tuple[str, str]] = []

    for bullet in bullets[:max_bullets]:
        improved = improve_bullet(bullet)
        if improved != bullet:
            suggestions.append((bullet, improved))

    return suggestions


__all__ = ["generate_rewrite_suggestions"]

