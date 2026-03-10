from typing import List

import nltk
import spacy
from nltk.corpus import stopwords


_SPACY_MODEL = "en_core_web_sm"
_nlp = None
_stopwords = None


def _ensure_resources() -> None:
    """
    Lazy-load spaCy model and NLTK resources.
    This function is intentionally idempotent.
    """
    global _nlp, _stopwords

    if _nlp is None:
        try:
            _nlp = spacy.load(_SPACY_MODEL)
        except OSError as exc:  # model not downloaded
            raise RuntimeError(
                f"spaCy model '{_SPACY_MODEL}' is not available. "
                f"Please run: python -m spacy download {_SPACY_MODEL}"
            ) from exc

    if _stopwords is None:
        try:
            nltk.data.find("corpora/stopwords")
        except LookupError:
            nltk.download("stopwords")
        _stopwords = set(stopwords.words("english"))


def preprocess_text(text: str) -> List[str]:
    """
    Basic NLP preprocessing: tokenization, lowercasing, stopword removal, lemmatization.

    Returns a list of lemmatized tokens suitable for downstream analysis.
    """
    if not text:
        return []

    _ensure_resources()
    doc = _nlp(text)

    tokens: List[str] = []
    for token in doc:
        if token.is_space or token.is_punct or token.like_url:
            continue
        lemma = token.lemma_.lower().strip()
        if not lemma or lemma in _stopwords:
            continue
        tokens.append(lemma)

    return tokens


def normalize_for_skill_matching(text: str) -> str:
    """
    Convenience helper to normalize text back into a processed string.
    """
    return " ".join(preprocess_text(text))


__all__ = ["preprocess_text", "normalize_for_skill_matching"]

