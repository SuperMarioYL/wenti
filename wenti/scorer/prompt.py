"""LLM-as-judge 评分 + rewrite 的 prompt 模板。

模板与 score.py 解耦：score.py 负责"调谁、传什么、解析什么"，
本模块负责"对模型说什么"。所有中文文案硬编码在这里，便于审阅与迭代。
"""

from __future__ import annotations

SCORE_SYSTEM = (
    "你是一位资深中文长文编辑，精通三联生活周刊体的文体判断。"
    "你只按给定 rubric 的维度打分，每个维度 0-5 分（一位小数），"
    "并给出三联体 voiced 的 rewrite 建议。打分要有区分度：bare-model 通用稿应明显低于"
    "三联体 pack 输出。不要奉承，不要给满分。"
)

SCORE_USER_TMPL = """\
文体 pack：
{pack_block}

rubric（0-5，权重见下）：
{rubric_block}

待打分草稿：
\"\"\"
{draft}
\"\"\"

请只输出一段 JSON（不要 markdown 代码块，不要前后文字），结构：
{{
  "sub_scores": {{"句式": <0-5>, "用词": <0-5>, "节奏": <0-5>, "视角": <0-5>}},
  "suggestions": [
    {{"dim": "句式|用词|节奏|视角", "issue": "<一句话指出问题>", "rewrite": "<三联体 voiced 的重写片段>"}}
  ]
}}
suggestions 最多 3 条，每条必须指向一个维度，rewrite 必须是可直接替换的三联体片段。
"""

REWRITE_SYSTEM = (
    "你是一位三联生活周刊体的撰稿人。按给定 pack 的 voice card 与 few-shots，"
    "把输入草稿重写成三联体：长句铺陈 + 短句收束，具象细节先于判断，"
    "第一人称旁观，具体时空坐标，不替读者下结论。保持原意，只换文体。"
)

REWRITE_USER_TMPL = """\
文体 pack：
{pack_block}

把下面的草稿重写成三联体（保留信息，只换文体；不要逐句翻译，要段落级重写）：

{draft}
"""


def render_rubric_block(rubric: dict) -> str:
    """Render the rubric dimensions as a compact prompt block."""
    lines = []
    for dim, spec in rubric["dimensions"].items():
        w = spec.get("weight", 0)
        lines.append(f"- {dim}（权重 {w}）：{spec.get('desc', '')}")
        if spec.get("pass"):
            lines.append(f"    过线：{spec['pass']}")
        if spec.get("fail"):
            lines.append(f"    不过线：{spec['fail']}")
    return "\n".join(lines)


def build_score_prompt(pack_block: str, rubric_block: str, draft: str) -> str:
    return SCORE_USER_TMPL.format(
        pack_block=pack_block, rubric_block=rubric_block, draft=draft
    )


def build_rewrite_prompt(pack_block: str, draft: str) -> str:
    return REWRITE_USER_TMPL.format(pack_block=pack_block, draft=draft)


__all__ = [
    "SCORE_SYSTEM",
    "SCORE_USER_TMPL",
    "REWRITE_SYSTEM",
    "REWRITE_USER_TMPL",
    "render_rubric_block",
    "build_score_prompt",
    "build_rewrite_prompt",
]
