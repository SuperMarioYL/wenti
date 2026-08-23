"""风格评分 scorer package — re-export the public surface."""

from .score import (
    ScoreReport,
    Suggestion,
    load_rubric,
    rewrite_draft,
    score_draft,
)

__all__ = ["ScoreReport", "Suggestion", "load_rubric", "score_draft", "rewrite_draft"]
