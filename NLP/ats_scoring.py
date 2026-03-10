from dataclasses import dataclass
from typing import List


@dataclass
class ATSScoreBreakdown:
    overall_score: float
    semantic_similarity: float
    skill_match_pct: float
    keyword_relevance: float
    matched_skills: List[str]
    missing_skills: List[str]
    matched_keywords: List[str]
    missing_keywords: List[str]
    # Extra transparency fields
    raw_score_before_gap_penalty: float
    gap_penalty_factor: float


def compute_keyword_relevance(
    resume_text: str,
    job_description: str,
    top_n: int = 20,
) -> tuple[float, list[str], list[str]]:
    """
    Very lightweight keyword relevance based on overlapping keywords
    between job description and resume.
    """
    from preprocessing import preprocess_text

    resume_tokens = set(preprocess_text(resume_text))
    jd_tokens = preprocess_text(job_description)

    # Heuristic: most frequent content tokens in JD
    freq: dict[str, int] = {}
    for tok in jd_tokens:
        freq[tok] = freq.get(tok, 0) + 1

    sorted_terms = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    top_terms = [term for term, _ in sorted_terms[:top_n]]
    top_set = set(top_terms)

    matched_keywords = sorted(top_set & resume_tokens)
    missing_keywords = sorted(top_set - resume_tokens)

    relevance = (
        len(matched_keywords) / len(top_set) if top_set else 0.0
    )
    return relevance, matched_keywords, missing_keywords


def compute_ats_score(
    semantic_similarity: float,
    skill_match_pct: float,
    keyword_relevance: float,
    matched_skills: List[str],
    missing_skills: List[str],
    matched_keywords: List[str],
    missing_keywords: List[str],
    w_semantic: float = 0.5,
    w_skills: float = 0.3,
    w_keywords: float = 0.2,
) -> ATSScoreBreakdown:
    """
    Combine different factors into an ATS score out of 100.
    Weights can be tuned depending on how important each factor is.
    """
    # Ensure weights sum to 1
    total_w = w_semantic + w_skills + w_keywords
    if total_w <= 0:
        raise ValueError("Sum of weights must be positive.")

    w_semantic /= total_w
    w_skills /= total_w
    w_keywords /= total_w

    semantic_norm = max(0.0, min(1.0, semantic_similarity))
    skills_norm = max(0.0, min(1.0, skill_match_pct))
    keywords_norm = max(0.0, min(1.0, keyword_relevance))

    score_0_1 = (
        w_semantic * semantic_norm
        + w_skills * skills_norm
        + w_keywords * keywords_norm
    )

    # Gap-aware penalty: if many required skills are missing, we dampen
    # the overall score even when semantic similarity is high.
    total_skills = len(matched_skills) + len(missing_skills)
    if total_skills > 0:
        missing_ratio = len(missing_skills) / total_skills
    else:
        missing_ratio = 0.0

    # Up to 35% penalty when all required skills are missing.
    gap_penalty_factor = 1.0 - 0.35 * missing_ratio
    gap_penalty_factor = max(0.65, min(1.0, gap_penalty_factor))

    raw_score_before_penalty = score_0_1
    score_0_1 *= gap_penalty_factor

    score_100 = round(score_0_1 * 100, 2)

    return ATSScoreBreakdown(
        overall_score=score_100,
        semantic_similarity=round(semantic_norm * 100, 2),
        skill_match_pct=round(skills_norm * 100, 2),
        keyword_relevance=round(keywords_norm * 100, 2),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        raw_score_before_gap_penalty=round(raw_score_before_penalty * 100, 2),
        gap_penalty_factor=round(gap_penalty_factor, 3),
    )


__all__ = ["ATSScoreBreakdown", "compute_keyword_relevance", "compute_ats_score"]

