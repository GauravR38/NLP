from dataclasses import dataclass
from typing import Dict, List

from semantic_matching import compute_semantic_similarity
from skill_extraction import extract_skills, skill_match_analysis
from ats_scoring import compute_keyword_relevance


SECTION_ALIASES: Dict[str, List[str]] = {
    "summary": ["summary", "profile", "about"],
    "skills": ["skills", "technical skills", "key skills"],
    "experience": ["experience", "work experience", "professional experience"],
    "projects": ["projects", "personal projects"],
    "education": ["education", "academic background"],
}


@dataclass
class SectionScore:
    name: str
    semantic_similarity: float  # 0–100
    skill_match_pct: float  # 0–100
    keyword_relevance: float  # 0–100
    overall_section_score: float  # 0–100


def detect_sections(resume_text: str) -> Dict[str, str]:
    """
    Very simple heuristic section splitter based on uppercase headings
    and known section aliases.
    """
    lines = resume_text.splitlines()
    sections: Dict[str, List[str]] = {}
    current_key = "other"

    def normalise_heading(h: str) -> str:
        h_norm = h.lower().strip(": ").strip()
        for canonical, aliases in SECTION_ALIASES.items():
            for alias in aliases:
                if alias in h_norm:
                    return canonical
        return "other"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Heading heuristic: short, mostly uppercase or followed by colon
        if (
            len(stripped) <= 40
            and (stripped.isupper() or stripped.endswith(":"))
        ):
            current_key = normalise_heading(stripped)
            if current_key not in sections:
                sections[current_key] = []
            continue

        sections.setdefault(current_key, []).append(stripped)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


def score_sections_against_jd(
    resume_text: str,
    job_description: str,
    required_skills: List[str],
) -> List[SectionScore]:
    """
    Compute a lightweight ATS-style score per detected section using
    semantic similarity, skill match, and keyword relevance.
    """
    sections = detect_sections(resume_text)
    results: List[SectionScore] = []

    for name, text in sections.items():
        if not text.strip():
            continue

        sim, _, _ = compute_semantic_similarity(text, job_description)
        section_resume_skills = extract_skills(text)
        matched, missing, match_pct = skill_match_analysis(
            section_resume_skills, required_skills
        )
        kw_rel, _, _ = compute_keyword_relevance(text, job_description)

        # Use lighter weights per section
        sim_pct = round(sim * 100, 2)
        skill_pct = round(match_pct * 100, 2)
        kw_pct = round(kw_rel * 100, 2)

        overall = round(
            0.5 * sim_pct + 0.3 * skill_pct + 0.2 * kw_pct, 2
        )

        results.append(
            SectionScore(
                name=name.capitalize(),
                semantic_similarity=sim_pct,
                skill_match_pct=skill_pct,
                keyword_relevance=kw_pct,
                overall_section_score=overall,
            )
        )

    # show core sections first
    priority_order = ["skills", "experience", "projects", "education", "summary", "other"]
    order_index = {name: i for i, name in enumerate(priority_order)}
    results.sort(
        key=lambda s: order_index.get(s.name.lower(), len(priority_order))
    )
    return results


__all__ = ["SectionScore", "detect_sections", "score_sections_against_jd"]

