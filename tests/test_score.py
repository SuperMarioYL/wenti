"""Wenti scorer contract tests — rubric parse + scorer shape + lift contract.

These run fully offline (dry-run path, no model call). They encode the m2
lift-gate in miniature: a bare-model draft must out-score-lower than a
三联体 pack draft on the same rubric, with 句式/用词/节奏 each improving.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wenti.packs import WentiPack, list_packs, load_pack
from wenti.scorer import load_rubric, score_draft
from wenti.scorer.score import ScoreReport, _heuristic_score

REPO = Path(__file__).resolve().parent.parent

BARE_DRAFT = (
    "随着人工智能的快速发展，越来越多的创作者开始使用 AI 工具辅助写作。"
    "AI 写作带来了很多便利。首先，AI 可以提升写作效率。其次，AI 能够降低"
    "创作门槛。最后，AI 有助于拓宽表达边界。\n\n"
    "AI 写作也面临一些挑战。一方面，AI 提供了便利。另一方面，过度依赖可能"
    "带来风险。总之，关键在于如何平衡。在当今社会，技术不断进步，我们需要"
    "与时俱进。\n\n"
    "综上所述，AI 写作是大势所趋。因此，我们应该积极拥抱这一变化。然而，"
    "也有人担心同质化。不可否认，这是值得注意的问题。不仅如此，而且要善于"
    "利用工具。"
)

SANLIAN_DRAFT = (
    "清晨五点四十，菜市场第一缕灯光亮起的时候，老周已经在摊位前站了二十分钟。"
    "他不吆喝。白菜码得齐整，像一摞没拆封的信，水汽从叶脉上慢慢爬下来。"
    "这是他在那条街的第三十七个冬天。\n\n"
    "我是在一个下过雨的下午认识这家店的。门脸小，招牌上的字掉了一半漆，"
    "剩一个\"记\"字，孤零零悬在那里。老板娘说，店是 1998 年开的，那一年她"
    "女儿刚上小学。现在女儿在上海，做金融，一年回来两次。\"她让我关店，\""
    "老板娘笑了一下，\"我说再开几年。开到开不动为止。\"\n\n"
    "城市在拆，也在长。工地围挡后面，一栋新楼正在往上够，钢筋扎得密，"
    "像倒立的树根。骑三轮的人从围挡下过，抬头看了一眼，没停。他赶着去送一单"
    "外卖，超时要扣钱。这座城里这样的人有几十万，他们不读三联，但三联关心他们"
    "走过的那条街，在下午四点的光里，是什么样子。\n\n"
    "黄昏是把一座城变得温柔的东西。写字楼的灯一盏一盏亮起来，像棋盘上落下的子。"
    "没有人说话，但所有人都在往前走。这种沉默的、被时间推着的走法，是这座城市"
    "最日常的样子，也是它最容易被忘记的样子。"
)


# --- rubric parse ----------------------------------------------------------


def test_rubric_loads_with_four_dimensions():
    rubric = load_rubric()
    assert rubric["scale"]["min"] == 0
    assert rubric["scale"]["max"] == 5
    dims = rubric["dimensions"]
    assert set(dims) == {"句式", "用词", "节奏", "视角"}


def test_rubric_weights_sum_to_one():
    rubric = load_rubric()
    total_w = sum(d.get("weight", 0) for d in rubric["dimensions"].values())
    assert abs(total_w - 1.0) < 1e-6


def test_each_dimension_has_pass_fail_criteria():
    rubric = load_rubric()
    for dim, spec in rubric["dimensions"].items():
        assert spec.get("weight", 0) > 0, f"{dim} missing weight"
        assert spec.get("desc"), f"{dim} missing desc"
        assert spec.get("pass"), f"{dim} missing pass criteria"
        assert spec.get("fail"), f"{dim} missing fail criteria"


# --- pack loader -----------------------------------------------------------


def test_index_lists_sanlian_as_default_free_pack():
    packs = list_packs()
    names = [p["name"] for p in packs]
    assert "sanlian" in names
    sanlian = next(p for p in packs if p["name"] == "sanlian")
    assert sanlian["lineage"] == "三联生活周刊体"
    assert sanlian["available"] is True
    assert sanlian["premium"] is False


def test_sanlian_pack_has_voice_card_and_few_shots():
    pack = load_pack("sanlian")
    assert isinstance(pack, WentiPack)
    assert pack.name == "sanlian"
    assert pack.lineage == "三联生活周刊体"
    assert pack.voice_card.strip(), "voice card must not be empty"
    assert len(pack.few_shots) >= 3, "三联体 pack must carry >=3 curated few-shots"
    for shot in pack.few_shots:
        assert shot.text.strip(), "few-shot text must not be empty"
    # the prompt block must surface voice card + every few-shot
    block = pack.to_prompt_block()
    assert pack.voice_card.strip()[:20] in block
    assert all(s.text.strip()[:20] in block for s in pack.few_shots)


def test_loading_unknown_pack_raises():
    with pytest.raises(FileNotFoundError):
        load_pack("nonexistent-pack-xyz")


# --- scorer contract -------------------------------------------------------


@pytest.fixture(scope="module")
def pack():
    return load_pack("sanlian")


@pytest.fixture(scope="module")
def rubric():
    return load_rubric()


def test_dry_run_is_default_when_no_env(monkeypatch, pack, rubric):
    monkeypatch.delenv("WENTI_BASE_URL", raising=False)
    monkeypatch.delenv("WENTI_API_KEY", raising=False)
    report = score_draft(BARE_DRAFT, pack, rubric)
    assert report.dry_run is True


def test_score_report_shape(pack, rubric):
    report = score_draft(SANLIAN_DRAFT, pack, rubric, dry_run=True)
    assert isinstance(report, ScoreReport)
    assert report.pack == "sanlian"
    assert set(report.sub_scores) == {"句式", "用词", "节奏", "视角"}
    for v in report.sub_scores.values():
        assert 0.0 <= v <= 5.0
    assert 0.0 <= report.total <= 5.0
    # total must equal the weighted sum
    expected = sum(
        report.sub_scores[d] * rubric["dimensions"][d]["weight"]
        for d in rubric["dimensions"]
    )
    assert abs(report.total - round(expected, 2)) < 1e-6
    assert report.dry_run is True
    assert isinstance(report.suggestions, list)
    assert 0 <= len(report.suggestions) <= 3
    for s in report.suggestions:
        assert s.dim in {"句式", "用词", "节奏", "视角"}
        assert s.issue
        assert s.rewrite


def test_dry_run_is_deterministic(pack, rubric):
    r1 = score_draft(SANLIAN_DRAFT, pack, rubric, dry_run=True)
    r2 = score_draft(SANLIAN_DRAFT, pack, rubric, dry_run=True)
    assert r1.sub_scores == r2.sub_scores
    assert r1.total == r2.total


# --- the lift-gate (m2 falsifier, in miniature) ---------------------------


def test_rubric_discriminates_bare_vs_sanlian(pack, rubric):
    """The m2 lift-gate: 文体-pack output must out-score bare-model output
    by >=0.5 total, with 句式/用词/节奏 each improving."""
    bare = score_draft(BARE_DRAFT, pack, rubric, dry_run=True)
    styled = score_draft(SANLIAN_DRAFT, pack, rubric, dry_run=True)

    assert styled.total - bare.total >= 0.5, (
        f"lift-gate failed: bare={bare.total} styled={styled.total} "
        f"delta={styled.total - bare.total:.2f} < 0.5"
    )
    for dim in ("句式", "用词", "节奏"):
        assert styled.sub_scores[dim] > bare.sub_scores[dim], (
            f"{dim} did not improve: bare={bare.sub_scores[dim]} "
            f"styled={styled.sub_scores[dim]}"
        )


def test_bare_draft_scores_low(pack, rubric):
    bare = score_draft(BARE_DRAFT, pack, rubric, dry_run=True)
    # a fully-slop draft should land well below the 三联体 floor
    assert bare.total < 2.5


def test_sanlian_draft_scores_above_three(pack, rubric):
    styled = score_draft(SANLIAN_DRAFT, pack, rubric, dry_run=True)
    assert styled.total >= 3.5


# --- suggestion targeting (v0.2.0: the two LOWEST dims, not the first two) --


def test_suggestions_target_two_lowest_dims(pack, rubric):
    """Suggestions must address the two lowest-scoring dimensions, not the
    first two in rubric order. On the styled draft 节奏 (2.6) is the weakest
    yet pre-v0.2.0 suggestions always named 句式/用词."""
    report = score_draft(SANLIAN_DRAFT, pack, rubric, dry_run=True)
    lowest = sorted(report.sub_scores.items(), key=lambda kv: kv[1])[:2]
    assert sorted(s.dim for s in report.suggestions) == sorted(d for d, _ in lowest)
    # the concrete case: 节奏 must be addressed, 用词 (a high scorer) must not
    dims = {s.dim for s in report.suggestions}
    assert "节奏" in dims
    assert "用词" not in dims


def test_suggestions_lowest_dims_on_bare_draft(pack, rubric):
    """The bare draft's two lowest ARE 句式/用词 — the pre-v0.2.0 output
    happened to be right here; it must stay right."""
    report = score_draft(BARE_DRAFT, pack, rubric, dry_run=True)
    lowest = sorted(report.sub_scores.items(), key=lambda kv: kv[1])[:2]
    assert sorted(s.dim for s in report.suggestions) == sorted(d for d, _ in lowest)


def test_suggestions_tie_break_follows_rubric_order(pack, rubric):
    """Tied scores resolve deterministically in rubric insertion order."""
    from wenti.scorer.score import Suggestion, _heuristic_suggestions

    notes = {"句式": ["a"], "用词": ["b"], "节奏": ["c"], "视角": ["d"]}
    sub_scores = {"句式": 2.0, "用词": 2.0, "节奏": 1.0, "视角": 4.0}
    out = _heuristic_suggestions(notes, sub_scores, pack)
    assert [s.dim for s in out] == ["节奏", "句式"]


# --- model path contract (v0.2.0: clamp + tolerant extraction) --------------


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content: str):
        self._content = content

    def create(self, **kw):
        return _FakeResponse(self._content)


class _FakeChat:
    def __init__(self, content: str):
        self.completions = _FakeCompletions(content)


class _FakeClient:
    """Mimics the OpenAI-compatible surface score.py calls:
    client.chat.completions.create(...) -> .choices[0].message.content"""

    def __init__(self, content: str):
        self.chat = _FakeChat(content)


def test_model_scores_clamped_to_rubric_scale(pack, rubric):
    """A judge that misreads the 0-5 scale (e.g. answers 0-10) must not break
    the ScoreReport 0-5 contract (schema.yaml)."""
    inflated = _FakeClient(
        '{"sub_scores": {"句式": 8.7, "用词": 9.2, "节奏": 7.5, "视角": 8.0},'
        ' "suggestions": []}'
    )
    r = score_draft("一段测试文本。", pack, rubric, dry_run=False, client=inflated)
    for v in r.sub_scores.values():
        assert 0.0 <= v <= 5.0
    assert r.total <= 5.0

    negative = _FakeClient(
        '{"sub_scores": {"句式": -3, "用词": 2, "节奏": 1, "视角": 0},'
        ' "suggestions": []}'
    )
    r = score_draft("一段测试文本。", pack, rubric, dry_run=False, client=negative)
    assert r.sub_scores["句式"] == 0.0

    in_range = _FakeClient(
        '{"sub_scores": {"句式": 3.5, "用词": 4.0, "节奏": 2.5, "视角": 3.0},'
        ' "suggestions": []}'
    )
    r = score_draft("一段测试文本。", pack, rubric, dry_run=False, client=in_range)
    assert r.sub_scores["句式"] == 3.5


def test_model_path_survives_fenced_json_with_trailing_prose(pack, rubric):
    """A fenced judge response with prose after the fence must still yield a
    report, not a JSONDecodeError traceback."""
    noisy = _FakeClient(
        '```json\n'
        '{"sub_scores": {"句式": 3.0, "用词": 4.0, "节奏": 2.5, "视角": 3.0},'
        ' "suggestions": [{"dim": "节奏", "issue": "段长偏均", "rewrite": "加短段收束"}]}'
        '\n```\n以上是评分结果。'
    )
    r = score_draft("一段测试文本。", pack, rubric, dry_run=False, client=noisy)
    assert r.dry_run is False
    assert r.sub_scores["用词"] == 4.0
    assert r.suggestions[0].dim == "节奏"


def test_extract_json_shapes():
    from wenti.scorer.score import _extract_json

    assert _extract_json('{"a": 1}') == {"a": 1}
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert _extract_json('```json\n{"a": 1}\n```\n以上是评分。') == {"a": 1}
    assert _extract_json('好的，这是评分结果：{"a": 2}') == {"a": 2}
