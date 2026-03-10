from typing import Dict, List, Tuple

from preprocessing import normalize_for_skill_matching


DEFAULT_SKILL_DICTIONARY: Dict[str, List[str]] = {
    # Programming Languages
    "python": ["python"],
    "java": ["java"],
    "javascript": ["javascript", "js"],
    "c++": ["c++"],
    "c#": ["c#"],
    "sql": ["sql"],
    "r": ["r programming", "r language"],
    "go": ["golang", "go"],
    # Data / ML / NLP
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "neural network", "neural networks"],
    "nlp": ["nlp", "natural language processing"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "spacy": ["spacy"],
    "nltk": ["nltk"],
    "transformers": ["transformers", "huggingface"],
    # Cloud / DevOps
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "ci/cd": ["ci/cd", "continuous integration", "continuous delivery"],
    # Tools / Misc
    "git": ["git", "version control"],
    "linux": ["linux"],
    "bash": ["bash", "shell scripting"],
    "jira": ["jira"],
    "excel": ["excel", "microsoft excel"],
}


def extract_skills(
    resume_text: str,
    skill_dictionary: Dict[str, List[str]] | None = None,
) -> List[str]:
    """
    Extract skills present in the resume using a simple dictionary-lookup approach.

    Parameters
    ----------
    resume_text : str
        The raw resume text.
    skill_dictionary : Dict[str, List[str]], optional
        Mapping from canonical skill names to lists of patterns/aliases.

    Returns
    -------
    List[str]
        Canonical skill names found in the resume.
    """
    if not resume_text:
        return []

    if skill_dictionary is None:
        skill_dictionary = DEFAULT_SKILL_DICTIONARY

    normalized = normalize_for_skill_matching(resume_text)

    found_skills: List[str] = []
    for skill, patterns in skill_dictionary.items():
        for pattern in patterns:
            pattern_norm = pattern.lower()
            if pattern_norm in normalized and skill not in found_skills:
                found_skills.append(skill)
                break

    return found_skills


def skill_match_analysis(
    resume_skills: List[str],
    required_skills: List[str],
) -> Tuple[List[str], List[str], float]:
    """
    Compute matched skills, missing skills, and match percentage.

    Returns
    -------
    matched : List[str]
    missing : List[str]
    match_pct : float
        Percentage in [0, 1].
    """
    resume_set = {s.lower() for s in resume_skills}
    required_set = {s.lower().strip() for s in required_skills if s.strip()}

    matched = sorted(resume_set & required_set)
    missing = sorted(required_set - resume_set)

    match_pct = len(matched) / len(required_set) if required_set else 0.0
    return matched, missing, match_pct


__all__ = [
    "DEFAULT_SKILL_DICTIONARY",
    "extract_skills",
    "skill_match_analysis",
]

