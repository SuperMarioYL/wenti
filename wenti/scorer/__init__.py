"""风格评分 scorer package — re-export the public surface."""

from .score import (
    ScoreReport,
    Suggestion,
    load_rubric,
    resolve_dry_run,
    rewrite_draft,
    score_draft,
)

__all__ = [
    "ScoreReport",
    "Suggestion",
    "load_rubric",
    "resolve_dry_run",
    "score_draft",
    "rewrite_draft",
]
