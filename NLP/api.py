from typing import List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ats_scoring import compute_ats_score, compute_keyword_relevance
from impact_scoring import compute_resume_impact_score
from resume_parser import extract_text_from_pdf
from rewriting_module import generate_rewrite_suggestions
from semantic_matching import compute_semantic_similarity
from section_analysis import score_sections_against_jd
from skill_extraction import DEFAULT_SKILL_DICTIONARY, extract_skills, skill_match_analysis
from skill_gap_analysis import analyze_skill_gaps, rank_job_description_skills


class AnalyzeResponse(BaseModel):
    ats_breakdown: dict
    section_scores: list
    jd_skill_rankings: list
    impact_breakdown: dict
    skill_gaps: list
    resume_skills: List[str]
    rewrite_suggestions: List[dict]


app = FastAPI(title="ATS-Aware Resume Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    job_description: str = Form(...),
    required_skills_text: Optional[str] = Form(None),
    resume: UploadFile = File(...),
):
    resume_bytes = await resume.read()
    resume_text = extract_text_from_pdf(resume_bytes)

    if not resume_text.strip():
        raise ValueError("Could not extract text from uploaded resume.")

    # Semantic similarity
    sim_score, _, _ = compute_semantic_similarity(resume_text, job_description)

    # Skills
    resume_skills = extract_skills(
        resume_text, skill_dictionary=DEFAULT_SKILL_DICTIONARY
    )

    def _parse_required_skills(raw: Optional[str]) -> List[str]:
        if not raw:
            return []
        parts: List[str] = []
        for line in raw.splitlines():
            for piece in line.split(","):
                cleaned = piece.strip()
                if cleaned:
                    parts.append(cleaned.lower())
        return sorted(set(parts))

    if required_skills_text and required_skills_text.strip():
        required_skills = _parse_required_skills(required_skills_text)
    else:
        required_skills = extract_skills(
            job_description, skill_dictionary=DEFAULT_SKILL_DICTIONARY
        )

    matched_skills, missing_skills, skill_match_pct = skill_match_analysis(
        resume_skills, required_skills
    )

    # Skill gaps
    skill_gaps = analyze_skill_gaps(
        required_skills=required_skills,
        resume_skills=resume_skills,
        job_description=job_description,
    )

    # Keywords
    kw_relevance, matched_kw, missing_kw = compute_keyword_relevance(
        resume_text, job_description
    )

    # ATS score
    ats = compute_ats_score(
        semantic_similarity=sim_score,
        skill_match_pct=skill_match_pct,
        keyword_relevance=kw_relevance,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        matched_keywords=matched_kw,
        missing_keywords=missing_kw,
    )

    # Sections
    sections = score_sections_against_jd(
        resume_text=resume_text,
        job_description=job_description,
        required_skills=required_skills,
    )

    # JD skills
    jd_rankings = rank_job_description_skills(job_description)

    # Impact
    impact = compute_resume_impact_score(resume_text)

    # Rewrite suggestions
    rewrites = [
        {"original": orig, "improved": improved}
        for orig, improved in generate_rewrite_suggestions(resume_text)
    ]

    return AnalyzeResponse(
        ats_breakdown=ats.__dict__,
        section_scores=[s.__dict__ for s in sections],
        jd_skill_rankings=[
            {"skill": s, "frequency": f, "importance": imp}
            for s, f, imp in jd_rankings
        ],
        impact_breakdown=impact.__dict__,
        skill_gaps=[g.__dict__ for g in skill_gaps],
        resume_skills=resume_skills,
        rewrite_suggestions=rewrites,
    )


__all__ = ["app"]

