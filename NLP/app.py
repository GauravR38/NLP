import textwrap
from typing import List

import streamlit as st

from ats_scoring import (
    ATSScoreBreakdown,
    compute_ats_score,
    compute_keyword_relevance,
)
from impact_scoring import (
    ImpactScoreBreakdown,
    compute_resume_impact_score,
)
from resume_parser import extract_text_from_pdf
from rewriting_module import generate_rewrite_suggestions
from semantic_matching import compute_semantic_similarity
from section_analysis import SectionScore, score_sections_against_jd
from skill_extraction import (
    DEFAULT_SKILL_DICTIONARY,
    extract_skills,
    skill_match_analysis,
)
from skill_gap_analysis import (
    SkillGap,
    analyze_skill_gaps,
    rank_job_description_skills,
)


st.set_page_config(
    page_title="ATS-Aware Resume Intelligence & Rewriting System",
    layout="wide",
)


def _parse_required_skills(raw: str) -> List[str]:
    """
    Parse required skills from a comma- or newline-separated string.
    """
    if not raw:
        return []
    parts: List[str] = []
    for line in raw.splitlines():
        for piece in line.split(","):
            cleaned = piece.strip()
            if cleaned:
                parts.append(cleaned.lower())
    return sorted(set(parts))


def display_ats_breakdown(breakdown: ATSScoreBreakdown) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall ATS Score", f"{breakdown.overall_score}/100")
    col2.metric("Semantic Similarity", f"{breakdown.semantic_similarity}%")
    col3.metric("Skill Match", f"{breakdown.skill_match_pct}%")
    col4.metric("Keyword Relevance", f"{breakdown.keyword_relevance}%")

    with st.expander("Explainable Breakdown: Skills"):
        st.markdown("**Matched Skills**")
        if breakdown.matched_skills:
            st.write(", ".join(breakdown.matched_skills))
        else:
            st.write("No skills from the required list were found in the resume.")

        st.markdown("**Missing Skills**")
        if breakdown.missing_skills:
            st.write(", ".join(breakdown.missing_skills))
        else:
            st.write("No missing skills. Great alignment!")

    with st.expander("Explainable Breakdown: Keywords"):
        st.markdown("**Matched Keywords from Job Description**")
        if breakdown.matched_keywords:
            st.write(", ".join(breakdown.matched_keywords))
        else:
            st.write("No high-salience job description keywords detected in the resume.")

        st.markdown("**Missing High-Value Keywords**")
        if breakdown.missing_keywords:
            st.write(", ".join(breakdown.missing_keywords))
        else:
            st.write("No major missing keywords detected.")

    with st.expander("Advanced Scoring Details"):
        st.markdown("**Raw score before skill-gap penalty**")
        st.write(f"{breakdown.raw_score_before_gap_penalty}/100")
        st.markdown("**Skill-gap penalty factor**")
        st.write(
            f"{breakdown.gap_penalty_factor} "
            "(multiplier applied based on proportion of missing required skills)."
        )


def display_skill_gap_analysis(gaps: List[SkillGap]) -> None:
    if not gaps:
        st.info(
            "No significant skill gaps detected relative to the provided or inferred required skills."
        )
        return

    st.markdown("The most impactful missing skills are listed first.")

    for gap in gaps:
        with st.expander(
            f"{gap.skill}  —  importance {int(gap.importance * 100)}%"
        ):
            st.markdown("**Importance in Job Description**")
            st.write(
                f"Estimated importance: {int(gap.importance * 100)}% "
                f"(mentions in JD: {gap.frequency_in_jd})."
            )
            st.markdown("**Recommendation**")
            st.write(gap.recommendation)


def display_section_scores(section_scores: List[SectionScore]) -> None:
    if not section_scores:
        st.info(
            "No clear sections were detected. Ensure your resume uses headings like "
            "SKILLS, EXPERIENCE, PROJECTS, EDUCATION, etc."
        )
        return

    for section in section_scores:
        with st.container():
            st.markdown(f"### {section.name} section")
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            col1.metric("Section ATS", f"{section.overall_section_score}/100")
            col2.metric("Semantic match", f"{section.semantic_similarity}%")
            col3.metric("Skill match", f"{section.skill_match_pct}%")
            col4.metric("Keyword relevance", f"{section.keyword_relevance}%")
            st.progress(min(section.overall_section_score / 100.0, 1.0))
            st.markdown("---")


def display_jd_skill_importance(
    jd_rankings: List[tuple[str, int, float]], resume_skills: List[str]
) -> None:
    if not jd_rankings:
        st.info(
            "No technical skills from the predefined dictionary were detected in the job description."
        )
        return

    resume_set = {s.lower() for s in resume_skills}

    for skill, freq, importance in jd_rankings:
        present = skill.lower() in resume_set
        label = f"{skill} — importance {int(importance * 100)}%"
        if present:
            label += " (present in resume)"
        with st.expander(label):
            st.write(
                f"Mentions in job description: **{freq}**. "
                f"Estimated importance: **{int(importance * 100)}%**."
            )
            if not present:
                st.write(
                    "Consider adding a concrete example or project that demonstrates this skill "
                    "if you have relevant experience."
                )
            else:
                st.write(
                    "This important skill is already present in your resume. "
                    "Ensure it is easy for recruiters and ATS to find (e.g., in both Skills and Experience)."
                )


def display_impact_score(impact: ImpactScoreBreakdown) -> None:
    st.metric("Overall Resume Impact Score", f"{impact.overall_impact_score}/100")
    st.progress(min(impact.overall_impact_score / 100.0, 1.0))

    col1, col2, col3 = st.columns(3)
    col1.metric("Strong action-verb bullets", f"{impact.action_verb_density}%")
    col2.metric(
        "Quantified achievement bullets", f"{impact.quantified_achievement_density}%"
    )
    col3.metric(
        "Technical skill bullets", f"{impact.technical_skill_density}%"
    )
    st.caption(f"Estimated bullets/sentences analyzed: {impact.total_bullets}")


def main() -> None:
    st.title("ATS-Aware Resume Intelligence & Rewriting System")
    st.caption(
        "Analyze your resume against a job description, understand ATS compatibility, "
        "section-wise strengths, and get high-impact rewrite suggestions."
    )

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("1. Upload Resume (PDF)")
        uploaded_file = st.file_uploader(
            "Upload your resume in PDF format", type=["pdf"]
        )

        resume_text = ""
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            resume_text = extract_text_from_pdf(file_bytes)
            if not resume_text:
                st.error("Could not extract text from the uploaded PDF.")
            else:
                with st.expander("Preview Extracted Resume Text"):
                    st.text_area(
                        "Extracted Resume Text",
                        value=resume_text[:8000],
                        height=300,
                    )

    with col_right:
        st.subheader("2. Job Description")
        job_description = st.text_area(
            "Paste the job description here",
            height=260,
        )

        st.subheader("3. Required Skills (Optional Override)")
        st.caption(
            "Optionally provide required skills as comma- or newline-separated values. "
            "If left blank, the system will infer skills only from the job description text."
        )
        raw_required_skills = st.text_area(
            "Required Skills",
            height=120,
            placeholder="e.g. Python, machine learning, SQL, AWS",
        )

    st.markdown("---")
    analyze_clicked = st.button("Analyze Resume", type="primary")
    if analyze_clicked:
        if not uploaded_file or not resume_text:
            st.error("Please upload a valid resume PDF first.")
            return
        if not job_description.strip():
            st.error("Please paste a job description.")
            return

        with st.spinner(
            "Computing semantic similarity, ATS scores, section analysis, and skill gaps..."
        ):
            # 1. Semantic similarity
            sim_score, _, _ = compute_semantic_similarity(
                resume_text, job_description
            )

            # 2. Skill extraction and match
            resume_skills = extract_skills(
                resume_text, skill_dictionary=DEFAULT_SKILL_DICTIONARY
            )

            if raw_required_skills.strip():
                required_skills = _parse_required_skills(raw_required_skills)
            else:
                # Simple heuristic: also extract skills from job description text
                required_skills = extract_skills(
                    job_description, skill_dictionary=DEFAULT_SKILL_DICTIONARY
                )

            matched_skills, missing_skills, skill_match_pct = (
                skill_match_analysis(resume_skills, required_skills)
            )

            # 3. Skill gap analysis (missing skills ranked by importance in JD)
            skill_gaps = analyze_skill_gaps(
                required_skills=required_skills,
                resume_skills=resume_skills,
                job_description=job_description,
            )

            # 4. Keyword relevance
            kw_relevance, matched_kw, missing_kw = compute_keyword_relevance(
                resume_text, job_description
            )

            # 5. ATS score (now aware of missing-skill impact through a gap penalty)
            breakdown = compute_ats_score(
                semantic_similarity=sim_score,
                skill_match_pct=skill_match_pct,
                keyword_relevance=kw_relevance,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                matched_keywords=matched_kw,
                missing_keywords=missing_kw,
            )

            # 6. Section-wise scoring
            section_scores = score_sections_against_jd(
                resume_text=resume_text,
                job_description=job_description,
                required_skills=required_skills,
            )

            # 7. Job description skill importance ranking
            jd_rankings = rank_job_description_skills(job_description)

            # 8. Resume impact score
            impact = compute_resume_impact_score(resume_text)

        overview_tab, sections_tab, jd_skills_tab, impact_tab, rewrite_tab = st.tabs(
            [
                "ATS Overview",
                "Section-wise ATS",
                "Job Description Skills",
                "Resume Impact",
                "Rewrite Suggestions",
            ]
        )

        with overview_tab:
            st.subheader("ATS Compatibility Results")
            display_ats_breakdown(breakdown)

            st.subheader("Explainable Feedback Summary")
        parts = []
        if breakdown.matched_skills:
            parts.append(
                f"Your resume already covers key skills such as "
                f"{', '.join(breakdown.matched_skills[:8])}."
            )
        if breakdown.missing_skills:
            parts.append(
                f"Consider explicitly highlighting experience with missing skills like "
                f"{', '.join(breakdown.missing_skills[:8])} where applicable."
            )
        if breakdown.missing_keywords:
            parts.append(
                "Incorporate more of the job description's language by adding keywords like "
                f"{', '.join(breakdown.missing_keywords[:8])} when they truthfully reflect your work."
            )

            if not parts:
                parts.append(
                    "Your resume appears well aligned with this job description "
                    "from an ATS perspective."
                )

            st.write(textwrap.fill(" ".join(parts), width=90))

            st.markdown("---")
            st.subheader("Skill Gap Analysis (Required vs. Resume)")
            display_skill_gap_analysis(skill_gaps)

        with sections_tab:
            st.subheader("Section-wise ATS Scoring")
            display_section_scores(section_scores)

        with jd_skills_tab:
            st.subheader("Job Description Skill Importance")
            display_jd_skill_importance(jd_rankings, resume_skills)

        with impact_tab:
            st.subheader("Resume Impact Score")
            display_impact_score(impact)

        with rewrite_tab:
            st.subheader("Resume Rewriting Suggestions")
            suggestions = generate_rewrite_suggestions(resume_text)
            if not suggestions:
                st.info(
                    "No obvious weak bullet points were detected or your resume text "
                    "does not use bullet-like sentences."
                )
            else:
                for i, (orig, improved) in enumerate(suggestions, start=1):
                    with st.expander(f"Suggestion {i}"):
                        st.markdown("**Original**")
                        st.write(orig)
                        st.markdown("**Improved**")
                        st.write(improved)


if __name__ == "__main__":
    main()

