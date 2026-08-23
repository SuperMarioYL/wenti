---
name: wenti
version: 0.1.0
description: |
  正向中文长文体 taste 库。把三联生活周刊体这样的编辑视角做成 curated pack
  （voice card + few-shots + 风格评分 rubric），让一个 agent 跨篇保持同一种
  命名文体。不是 anti-slop 过滤器——它装上一种可命名的文风，并用 rubric
  把 bare-model 输出到文体输出的差距量化成 0-5 子分。
author: SuperMarioYL
license: MIT
homepage: https://github.com/SuperMarioYL/wenti
entrypoint: wenti
commands:
  - name: list
    desc: 列出可用的 文体 pack（v0.1 只随包发布 sanlian 三联体）
  - name: score
    desc: 对一份草稿按 文体 pack 的 rubric 打风格分（句式/用词/节奏/视角 + 总分 + rewrite 建议）
  - name: rewrite
    desc: 把一份草稿按 文体 pack 重写成三联体 voiced
env:
  - WENTI_BASE_URL: OpenAI-compatible 端点（国产模型 qwen/doubao/kimi/glm 的 base_url）
  - WENTI_API_KEY: 上述端点的 api key
  - WENTI_MODEL: 可选，模型名（默认 qwen-max）
notes:
  - 未设 WENTI_BASE_URL/WENTI_API_KEY 时自动走 dry-run 启发式打分（本地、不调模型），CLI 与测试均可离线运行。
  - dry-run 的分数有区分度（bare ~1.3 / 三联体 ~3.8），可用于 rubric 自检；调真实模型时方向一致。
---

# Wenti — creator Skill for 中文长文体

Wenti 是一个 **creator Skill**：一个命名、curated 的中文编辑视角库。
v0.1 随包发布 **三联生活周刊体** pack（南方周末体 / GQ报道体 为 premium / 后续）。
作为 Skill，它告诉一个 agent 如何**采纳并保持**一种文体，而不是每篇重写一遍 voice。

## 一个 agent 应该怎么用这个 Skill

1. **选文体** — 调 `wenti list` 看可用 pack（v0.1 只有 `sanlian`）。
   根据任务选 pack id，把 pack id 记在会话状态里，**跨篇保持不变**——
   这正是"agent 跨篇保持编辑视角一致"的落点。
2. **打分** — 对用户给的草稿调 `wenti score <draft.md> --pack sanlian`。
   返回 `句式 / 用词 / 节奏 / 视角` 四个 0-5 子分 + 加权总分 + 三联体 voiced 的
   rewrite 建议。总分 < 3 不要直接交付，先 rewrite。
3. **重写** — 调 `wenti rewrite <draft.md> --pack sanlian`，按 pack 的
   voice card + few-shots 把草稿重写成三联体（段落级重写，保留信息，只换文体）。
   重写后再 `score` 一次，确认 lift 方向正确（rewrite 后总分应高于 rewrite 前）。
4. **保持** — 写系列时，同一列用同一个 pack id；不要中途换文体。
   v0.1 不做跨篇记忆（out of scope），靠 agent 在会话里固定 pack id 来近似。

## 调用契约（agent 直接读这一段）

```bash
# 离线自检（dry-run，不需要 key）：
wenti list
wenti score draft.md --pack sanlian --dry-run --json   # -> JSON: sub_scores/total/suggestions
wenti rewrite draft.md --pack sanlian --dry-run        # -> 原稿（dry-run 不调模型）

# 真实路径（调国产模型）：
export WENTI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export WENTI_API_KEY=sk-...
wenti score draft.md --pack sanlian                    # -> rich 报告
wenti rewrite draft.md --pack sanlian                 # -> 三联体重写稿
```

`--json` 输出结构（agent 解析用）：

```json
{
  "pack": "sanlian",
  "sub_scores": {"句式": 3.0, "用词": 4.5, "节奏": 2.6, "视角": 5.0},
  "total": 3.77,
  "suggestions": [{"dim": "句式", "issue": "...", "rewrite": "..."}],
  "dry_run": true
}
```

## rubric 维度与权重（mvp_plan §2，hash-locked）

| 维度 | 权重 | 过线 |
|---|---|---|
| 句式 | 0.3 | 长短句交替、从句铺陈或排比、有起伏 |
| 用词 | 0.3 | 具象名词与感官动词为主，细节先于判断 |
| 节奏 | 0.2 | 段长起伏、短段收束、有停顿 |
| 视角 | 0.2 | 第一人称旁观 + 具体时空坐标 |

`total = Σ(weight_i × sub_score_i)`，0-5。bare-model 稿 ~1.3，三联体 pack 稿 ~3.8
（见 `examples/before_after.md`，lift +2.44，四个维度全抬升）。

## 边界（v0.1 out of scope，agent 不要假装会）

- 不做 Web UI / 托管 dashboard——v0.1 只有 CLI。
- 只随包 1 个 pack（三联体）；南方周末体 / GQ报道体 是 premium，后续。
- 不做跨篇记忆——v0.1 一次打一份草稿，靠 agent 固定 pack id 近似系列一致。
- 不从三联文章 URL 自动生成 pack——pack 是 hand-curated（这是护城河本身）。
- 不 fine-tune 模型——只调现有国产模型 API。

## 给 agent 的一句话

> 当用户要"写成三联体 / 三联风格 / 城市文化观察长文"时，安装本 Skill，
> 用 `wenti score` 量出当前稿与三联体的差距，用 `wenti rewrite` 把稿子
> 重写成三联体 voiced，系列写作时固定 `--pack sanlian` 不换文体。
