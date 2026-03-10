import re
from dataclasses import dataclass
from typing import List

from rewriting_module import STRONG_VERBS
from skill_extraction import DEFAULT_SKILL_DICTIONARY


NUMBER_PATTERN = re.compile(r"\b\d+(\.\d+)?%?|\$\d+|\b\d{4}\b")


@dataclass
class ImpactScoreBreakdown:
    overall_impact_score: float
    action_verb_density: float
    quantified_achievement_density: float
    technical_skill_density: float
    total_bullets: int


def _extract_bullets(text: str) -> List[str]:
    bullets: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for prefix in ("- ", "* ", "• "):
            if line.startswith(prefix):
                line = line[len(prefix) :]
                break
        bullets.append(line)
    if not bullets:
        # fallback: treat sentences as bullets
        bullets = [s.strip() for s in text.split(".") if s.strip()]
    return bullets


def compute_resume_impact_score(resume_text: str) -> ImpactScoreBreakdown:
    """
    Heuristic "impact score" based on:
    - bullet lines starting with strong action verbs
    - quantified achievements (numbers / % / $)
    - explicit mentions of technical skills
    """
    bullets = _extract_bullets(resume_text)
    if not bullets:
        return ImpactScoreBreakdown(
            overall_impact_score=0.0,
            action_verb_density=0.0,
            quantified_achievement_density=0.0,
            technical_skill_density=0.0,
            total_bullets=0,
        )

    total = len(bullets)
    strong_verb_count = 0
    quantified_count = 0
    tech_skill_count = 0

    strong_verbs_lower = [v.lower() for v in STRONG_VERBS]
    tech_terms = set()
    for patterns in DEFAULT_SKILL_DICTIONARY.values():
        for p in patterns:
            tech_terms.add(p.lower())

    for bullet in bullets:
        lowered = bullet.lower()

        # strong verbs at start
        if any(lowered.startswith(v + " ") for v in strong_verbs_lower):
            strong_verb_count += 1

        # quantified achievements
        if NUMBER_PATTERN.search(bullet):
            quantified_count += 1

        # technical skills
        if any(term in lowered for term in tech_terms):
            tech_skill_count += 1

    action_density = strong_verb_count / total
    quantified_density = quantified_count / total
    tech_density = tech_skill_count / total

    # combine with simple weights
    overall = (
        0.4 * action_density + 0.35 * quantified_density + 0.25 * tech_density
    ) * 100.0

    return ImpactScoreBreakdown(
        overall_impact_score=round(overall, 2),
        action_verb_density=round(action_density * 100, 2),
        quantified_achievement_density=round(quantified_density * 100, 2),
        technical_skill_density=round(tech_density * 100, 2),
        total_bullets=total,
    )


__all__ = ["ImpactScoreBreakdown", "compute_resume_impact_score"]

