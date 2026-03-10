from dataclasses import dataclass
from typing import List, Tuple

from preprocessing import normalize_for_skill_matching
from skill_extraction import DEFAULT_SKILL_DICTIONARY, extract_skills


@dataclass
class SkillGap:
    """
    Represents a missing skill from the job description along with
    an importance signal derived from the job description text.
    """

    skill: str
    importance: float  # 0–1 importance based on frequency/salience in JD
    frequency_in_jd: int
    recommendation: str


def analyze_skill_gaps(
    required_skills: List[str],
    resume_skills: List[str],
    job_description: str,
) -> List[SkillGap]:
    """
    Highlight missing skills from the job description with an importance score.

    Importance is estimated heuristically using how often a skill term appears
    (or is referenced) in the job description. This is not perfect but helps
    surface the highest-impact missing skills first.
    """
    if not required_skills:
        return []

    normalized_jd = normalize_for_skill_matching(job_description or "")
    jd_tokens = normalized_jd.split()
    jd_text_for_phrase = f" {normalized_jd} "

    resume_set = {s.lower().strip() for s in resume_skills}

    gaps: List[SkillGap] = []

    for raw_skill in required_skills:
        skill = raw_skill.lower().strip()
        if not skill:
            continue
        if skill in resume_set:
            continue

        # Count both token-level and phrase-level occurrences
        token_freq = jd_tokens.count(skill)
        phrase_freq = jd_text_for_phrase.count(f" {skill} ")
        freq = max(token_freq, phrase_freq)

        # Map frequency to importance in [0, 1]
        if freq == 0:
            importance = 0.3  # skill is listed but not repeated; still relevant
        elif freq == 1:
            importance = 0.6
        elif freq == 2:
            importance = 0.8
        else:
            importance = 1.0

        if importance >= 0.8:
            recommendation = (
                f"Add at least one clear bullet describing hands-on experience with '{raw_skill}' "
                "since it appears multiple times in the job description."
            )
        elif importance >= 0.6:
            recommendation = (
                f"Consider mentioning '{raw_skill}' explicitly in a relevant project or experience section."
            )
        else:
            recommendation = (
                f"If you have exposure to '{raw_skill}', reference it in a summary or skills section."
            )

        gaps.append(
            SkillGap(
                skill=raw_skill,
                importance=round(importance, 2),
                frequency_in_jd=freq,
                recommendation=recommendation,
            )
        )

    gaps.sort(key=lambda g: (g.importance, g.frequency_in_jd), reverse=True)
    return gaps


def rank_job_description_skills(
    job_description: str,
) -> List[Tuple[str, int, float]]:
    """
    Extract skills from the job description and rank them by frequency / importance.

    Returns a list of (skill, frequency, importance) sorted descending.
    """
    normalized_jd = normalize_for_skill_matching(job_description or "")
    jd_tokens = normalized_jd.split()
    jd_text_for_phrase = f" {normalized_jd} "

    skills_in_jd = extract_skills(
        job_description, skill_dictionary=DEFAULT_SKILL_DICTIONARY
    )

    rankings: List[Tuple[str, int, float]] = []
    for skill in skills_in_jd:
        skill_l = skill.lower()
        token_freq = jd_tokens.count(skill_l)
        phrase_freq = jd_text_for_phrase.count(f" {skill_l} ")
        freq = max(token_freq, phrase_freq)

        if freq == 0:
            importance = 0.4
        elif freq == 1:
            importance = 0.6
        elif freq == 2:
            importance = 0.8
        else:
            importance = 1.0

        rankings.append((skill, freq, round(importance, 2)))

    rankings.sort(key=lambda x: (x[2], x[1]), reverse=True)
    return rankings


__all__ = ["SkillGap", "analyze_skill_gaps", "rank_job_description_skills"]


