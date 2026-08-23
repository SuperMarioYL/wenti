"""风格评分 scorer core — pack + draft + rubric -> sub_scores + suggestions.

Two execution paths:

* **model path** — calls an OpenAI-compatible endpoint (qwen / doubao / kimi / glm
  via ``base_url`` override). ``WENTI_BASE_URL`` + ``WENTI_API_KEY`` must be set.
* **dry-run path** — a deterministic local heuristic that scores without a model
  call, so the CLI and tests run offline. It is deliberately sensitive to the
  三联体 voice markers in the few-shots, so a 文体-pack draft outscores a
  bare-model draft on the same rubric (the m2 lift-gate, in miniature).

The dry-run path is the v0.1 falsifiability floor: if even the heuristic cannot
discriminate bare vs. 文体, the rubric is broken before any model is called.
"""

from __future__ import annotations

import json
import os
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..packs import WentiPack
from . import prompt as prompt_mod

_RUBRIC_PATH = Path(__file__).resolve().parent / "rubric.yaml"


@dataclass
class Suggestion:
    dim: str
    issue: str
    rewrite: str


@dataclass
class ScoreReport:
    pack: str
    draft: str
    sub_scores: dict[str, float]
    total: float
    suggestions: list[Suggestion] = field(default_factory=list)
    dry_run: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack": self.pack,
            "draft": self.draft,
            "sub_scores": dict(self.sub_scores),
            "total": round(self.total, 2),
            "suggestions": [s.__dict__ for s in self.suggestions],
            "dry_run": self.dry_run,
        }


def load_rubric(path: Path | None = None) -> dict[str, Any]:
    """Load the 风格评分 rubric YAML."""
    rubric_path = path or _RUBRIC_PATH
    return yaml.safe_load(rubric_path.read_text(encoding="utf-8")) or {}


def _clamp(x: float, lo: float = 0.0, hi: float = 5.0) -> float:
    return max(lo, min(hi, x))


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"[。！？!?]", text)
    return [p.strip() for p in parts if p.strip()]


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


# 三联体 voice markers — derived from the few-shots' concrete vocabulary.
_VOICE_TOKENS = (
    "城市", "日常", "细节", "时代", "记忆", "时间", "街道", "黄昏", "人群",
    "屋檐", "缝隙", "沉默", "喧哗", "气味", "光线", "褶皱", "摊位", "白菜",
    "写字楼", "地铁", "便利店", "三轮", "围挡", "钢筋", "棋盘", "菜场",
    "菜市场", "招牌", "黄昏", "下午", "清晨", "冬天", "女儿", "老板娘",
    "老周", "信", "水汽", "叶脉", "饭", "水", "灯", "光",
)

_SENSORY_VERBS = ("亮起", "爬", "翻", "落", "涌", "推", "码", "悬", "调", "够", "扎")

# AI-slop 套话 — bare-model drafts leak these.
_SLOP_PATTERNS = (
    "综上所述", "总而言之", "首先", "其次", "最后", "在当今社会",
    "随着", "众所周知", "不可否认", "显而易见", "值得注意", "总之",
    "不仅", "而且", "因此", "然而", "一方面", "另一方面",
)


def _score_jushi(text: str) -> tuple[float, list[str]]:
    sents = _split_sentences(text)
    if not sents:
        return 0.5, ["全文无完整句。"]
    lens = [len(s) for s in sents]
    mean = statistics.mean(lens)
    stdev = statistics.pstdev(lens) if len(lens) > 1 else 0.0
    long_sents = sum(1 for n in lens if n >= 40)
    questions = text.count("？") + text.count("?")
    # connective-first sentences (首先/其次/因此……) are the "5-段 essay" slop
    # signature; 三联体 varies its sentence openings.
    connective_openers = (
        "首先", "其次", "最后", "总之", "因此", "然而", "一方面", "另一方面",
        "综上所述", "不可否认", "由此可见", "不仅如此",
    )
    connective_first = sum(1 for s in sents if s.startswith(connective_openers))
    notes: list[str] = []
    score = 1.5
    if stdev >= 20:
        score += 1.5
        notes.append(f"句长起伏大（σ={stdev:.0f}）")
    elif stdev >= 10:
        score += 1.0
        notes.append(f"句长有起伏（σ={stdev:.0f}）")
    else:
        notes.append("句长偏均，节奏平直")
    if long_sents >= 1:
        score += 1.0
        notes.append(f"有 {long_sents} 处长句铺陈")
    if questions >= 1:
        score += min(1.0, questions * 0.5)
        notes.append(f"设问 {questions} 处")
    if connective_first >= 1:
        score -= min(1.2, connective_first * 0.3)
        notes.append(f"连接词起句 {connective_first} 处（-0.3/处）")
    # choppy penalty
    if mean < 12 and len(sents) >= 3:
        score -= 1.0
        notes.append("全篇短句，缺铺陈")
    return _clamp(score), notes


def _score_yongci(text: str) -> tuple[float, list[str]]:
    voice_hits = sum(text.count(t) for t in _VOICE_TOKENS)
    slop_hits = sum(len(re.findall(p, text)) for p in _SLOP_PATTERNS)
    sensory_hits = sum(text.count(v) for v in _SENSORY_VERBS)
    notes: list[str] = []
    score = 1.5
    score += min(2.3, voice_hits * 0.25)
    if voice_hits:
        notes.append(f"具象/感官词 {voice_hits} 处")
    score += min(0.7, sensory_hits * 0.3)
    if sensory_hits:
        notes.append(f"感官动词 {sensory_hits} 处")
    penalty = min(1.3, slop_hits * 0.5)
    score -= penalty
    if slop_hits:
        notes.append(f"AI-slop 套话 {slop_hits} 处（-{penalty:.1f}）")
    if voice_hits == 0 and sensory_hits == 0:
        notes.append("无具象细节，全篇抽象")
    return _clamp(score), notes


def _score_jiezou(text: str) -> tuple[float, list[str]]:
    paras = _split_paragraphs(text)
    if not paras:
        return 0.5, ["无段落结构。"]
    lens = [len(p) for p in paras]
    stdev = statistics.pstdev(lens) if len(lens) > 1 else 0.0
    short_paras = sum(1 for n in lens if n <= 30)
    notes: list[str] = []
    score = 1.5
    if stdev >= 40:
        score += 1.0
        notes.append("段长起伏大")
    elif stdev >= 18:
        score += 0.6
        notes.append("段长有起伏")
    else:
        notes.append("段长偏均")
    score += min(1.5, short_paras * 0.5)
    if short_paras:
        notes.append(f"短段收束 {short_paras} 处")
    if len(paras) >= 3:
        score += 0.5
    return _clamp(score), notes


def _score_shijiao(text: str) -> tuple[float, list[str]]:
    first_person = text.count("我")
    time_place = sum(
        text.count(t)
        for t in (
            "那年", "那天", "当", "1998", "清晨", "下午", "黄昏", "五点",
            "菜市场", "店", "摊", "街", "地铁口", "写字楼", "围挡",
        )
    )
    proper = sum(text.count(n) for n in ("老周", "老板娘", "她", "他"))
    notes: list[str] = []
    score = 1.0
    if first_person >= 1:
        score += 1.0
        notes.append("第一人称旁观")
    else:
        score -= 0.5
        notes.append("缺第一人称，全知口吻")
    score += min(1.3, time_place * 0.4)
    if time_place:
        notes.append(f"具体时空坐标 {time_place} 处")
    score += min(1.2, proper * 0.35)
    if proper:
        notes.append(f"具体人物 {proper} 处")
    return _clamp(score), notes


def _heuristic_score(draft: str, pack: WentiPack, rubric: dict) -> ScoreReport:
    """Deterministic offline scorer — the dry-run path."""
    dims = rubric["dimensions"]
    scorers = {
        "句式": _score_jushi,
        "用词": _score_yongci,
        "节奏": _score_jiezou,
        "视角": _score_shijiao,
    }
    sub_scores: dict[str, float] = {}
    notes_by_dim: dict[str, list[str]] = {}
    for dim in dims:
        fn = scorers.get(dim)
        if fn is None:
            sub_scores[dim] = 2.5
            notes_by_dim[dim] = ["无对应启发式，给中位分"]
            continue
        s, notes = fn(draft)
        sub_scores[dim] = round(s, 2)
        notes_by_dim[dim] = notes
    total = _weighted_total(sub_scores, dims)
    suggestions = _heuristic_suggestions(notes_by_dim, pack)
    return ScoreReport(
        pack=pack.name,
        draft=draft,
        sub_scores=sub_scores,
        total=round(total, 2),
        suggestions=suggestions,
        dry_run=True,
    )


def _weighted_total(sub_scores: dict[str, float], dims: dict) -> float:
    return sum(sub_scores[d] * dims[d].get("weight", 0) for d in dims)


def _heuristic_suggestions(notes_by_dim: dict[str, list[str]], pack: WentiPack) -> list[Suggestion]:
    """Pick the two lowest-scoring dims and offer a voiced rewrite cue."""
    out: list[Suggestion] = []
    exemplar = pack.few_shots[0].text.strip()[:60] if pack.few_shots else ""
    for dim, notes in list(notes_by_dim.items())[:2]:
        issue = "；".join(notes) if notes else "该维度未过线"
        rewrite = (
            f"参考三联体范例开头改写：{exemplar}……"
            if exemplar
            else "按 voice card 改写：长句铺陈 + 短句收束，具象先于判断。"
        )
        out.append(Suggestion(dim=dim, issue=issue, rewrite=rewrite))
    return out


# --- model path -----------------------------------------------------------


def _extract_json(text: str) -> dict[str, Any]:
    """Tolerant JSON extraction from a model response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # fall back to first {...} block
    if not text.startswith("{"):
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            text = m.group(0)
    return json.loads(text)


def _build_client(base_url: str | None, api_key: str | None):
    from openai import OpenAI

    return OpenAI(
        base_url=base_url or os.environ.get("WENTI_BASE_URL"),
        api_key=api_key or os.environ.get("WENTI_API_KEY"),
    )


def _model_score(
    draft: str,
    pack: WentiPack,
    rubric: dict,
    client: Any,
    model: str,
) -> ScoreReport:
    rubric_block = prompt_mod.render_rubric_block(rubric)
    user = prompt_mod.build_score_prompt(
        pack_block=pack.to_prompt_block(),
        rubric_block=rubric_block,
        draft=draft,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt_mod.SCORE_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message.content or "{}"
    data = _extract_json(content)
    dims = rubric["dimensions"]
    sub_scores = {
        d: round(float(data.get("sub_scores", {}).get(d, 2.5)), 2) for d in dims
    }
    suggestions = [
        Suggestion(
            dim=s.get("dim", ""),
            issue=s.get("issue", ""),
            rewrite=s.get("rewrite", ""),
        )
        for s in (data.get("suggestions") or [])[:3]
    ]
    total = _weighted_total(sub_scores, dims)
    return ScoreReport(
        pack=pack.name,
        draft=draft,
        sub_scores=sub_scores,
        total=round(total, 2),
        suggestions=suggestions,
        dry_run=False,
    )


def _resolve_dry_run(dry_run: bool | None) -> bool:
    if dry_run is not None:
        return dry_run
    return not (os.environ.get("WENTI_BASE_URL") and os.environ.get("WENTI_API_KEY"))


def score_draft(
    draft: str,
    pack: WentiPack,
    rubric: dict | None = None,
    *,
    dry_run: bool | None = None,
    client: Any = None,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> ScoreReport:
    """Score a draft against a pack's rubric.

    Auto-detects dry-run when ``WENTI_BASE_URL`` / ``WENTI_API_KEY`` are unset
    *and* no client is passed in. Pass ``dry_run=True`` to force the offline
    heuristic (used by tests and the no-key CLI path).
    """
    rubric = rubric or load_rubric()
    use_dry = _resolve_dry_run(dry_run)
    if use_dry:
        return _heuristic_score(draft, pack, rubric)
    if client is None:
        client = _build_client(base_url, api_key)
    model = model or os.environ.get("WENTI_MODEL", "qwen-max")
    return _model_score(draft, pack, rubric, client, model)


def rewrite_draft(
    draft: str,
    pack: WentiPack,
    *,
    dry_run: bool | None = None,
    client: Any = None,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> str:
    """Rewrite a draft in the pack's voice. Returns the rewritten text."""
    use_dry = _resolve_dry_run(dry_run)
    if use_dry:
        # Honest no-model path: do not fake a rewrite. Return the original
        # with a banner so the user knows no model was called.
        return f"# [wenti dry-run] 未调用模型，原稿返回（设 WENTI_API_KEY/WENTI_BASE_URL 走真实 rewrite）\n\n{draft}"
    if client is None:
        client = _build_client(base_url, api_key)
    model = model or os.environ.get("WENTI_MODEL", "qwen-max")
    user = prompt_mod.build_rewrite_prompt(
        pack_block=pack.to_prompt_block(), draft=draft
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt_mod.REWRITE_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.6,
    )
    return (resp.choices[0].message.content or draft).strip()


__all__ = [
    "ScoreReport",
    "Suggestion",
    "load_rubric",
    "score_draft",
    "rewrite_draft",
]
