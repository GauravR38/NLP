from typing import Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def compute_semantic_similarity(
    resume_text: str,
    job_description: str,
) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Compute semantic similarity between resume and job description.

    Returns
    -------
    similarity : float
        Cosine similarity in [0, 1].
    resume_emb : np.ndarray
    jd_emb : np.ndarray
    """
    if not resume_text or not job_description:
        return 0.0, np.zeros(1), np.zeros(1)

    model = _get_model()
    embeddings = model.encode([resume_text, job_description])
    resume_emb, jd_emb = embeddings[0], embeddings[1]

    sim = cosine_similarity(
        resume_emb.reshape(1, -1), jd_emb.reshape(1, -1)
    )[0][0]

    # Normalise similarity to [0, 1] if model returns outside numerical bounds
    sim = float(max(0.0, min(1.0, sim)))
    return sim, resume_emb, jd_emb


__all__ = ["compute_semantic_similarity"]

