[English](./README.en.md) | **简体中文**

<div align="right"><sub><b>简体中文</b>&nbsp;&nbsp;⇄&nbsp;&nbsp;<a href="./README.en.md">English</a></sub></div>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/hero-light.svg">
  <img src="./assets/hero-light.svg" width="880" alt="Wenti — 正向中文长文体 taste 库">
</picture>

<p align="center"><sub>Wenti 是 Skill-native 的 taste 库：给 prosumer 公众号作者一种 curated 三联 voice。</sub></p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/github/license/SuperMarioYL/wenti?label=license" alt="license"></a>
  <a href="https://github.com/SuperMarioYL/wenti/releases"><img src="https://img.shields.io/github/v/release/SuperMarioYL/wenti?label=release" alt="release"></a>
  <a href="https://github.com/SuperMarioYL/wenti/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/SuperMarioYL/wenti/ci.yml?branch=main&label=CI" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white" alt="python">
  <img src="https://img.shields.io/badge/Skill-creator-5E5CE6" alt="Skill">
  <img src="https://img.shields.io/badge/Agent-voice--consistency-10A37F" alt="Agent">
</p>

**给 agent 装上一种可命名的中文长文体——不是 anti-slop 过滤器，是正向 taste 库。**

Skill 作为 agent 的 voice 载体正在成为主流：[taste-skill](https://github.com/Leonxlnx/taste-skill)（79k star）证明了"给 agent 装一种 voice"是被大规模采纳的产品形态。但它是**负向**的 anti-slop——去掉 AI 味，却不装上任何 named 文体，输出停在"不坏但也不是什么"。Wenti 是它的正向中文兄弟：把三联生活周刊体这样的编辑视角做成 hand-curated pack，一个 agent 跨篇保持同一种命名文体，风格评分 rubric 量出 bare-model 到文体输出的差距。内容审美 KOL [op7418](https://jike.city/op7418) 一直在讨论的"中文长文需要可命名的编辑视角"，正是这套 rubric 要量化的事；[HKUDS](https://github.com/HKUDS) 的 agent-capability 研究方向里，跨篇 voice-consistency 也是长期命题。

<h2><img src="https://api.iconify.design/tabler:topology-star-3.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> 架构</h2>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/atlas-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/atlas-light.svg">
  <img src="./assets/atlas-light.svg" width="880" alt="架构：SKILL.md → CLI → 文体 pack + rubric → 国产模型 → 风格评分报告">
</picture>

一个进程（typer CLI），一次外部 API 调用（国产模型 via base_url），零微服务。`SKILL.md` 是 CLI 的薄封装——agent 与人走**同一条**打分路径。

<h2><img src="https://api.iconify.design/tabler:bulb.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> 为什么做这个</h2>

公众号长文创作者今天能 prompt 一个 bare 模型拿到通用 AI 散文，或 bolt 上一个 anti-slop skill 拿到"不再是 slop 但也不是任何特定文体"的稿子。具体失败的瞬间：连载到第 5 篇时，想让它在同一套三联体编辑视角下读，却得每篇手动 re-voice。Wenti 把"采纳并保持一种 named 文体"做成可安装的 Skill——taste 库本身是产品，不是模型也不是通用过滤器。

<h2><img src="https://api.iconify.design/tabler:rocket.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> 快速开始</h2>

```bash
pipx install wenti                                    # 或 uv tool install wenti
export WENTI_BASE_URL=... WENTI_API_KEY=...           # 指向国产模型（qwen 默认）
wenti score my_draft.md --pack sanlian               # 句式/用词/节奏/视角 + 总分 + rewrite 建议
```

无 key 时自动走 dry-run 启发式打分（本地、离线、可复现），`wenti list` / `wenti score --dry-run` 开箱即用。

<details><summary>sample 输出（dry-run）</summary>

```
╭──────── 风格评分 · my_draft.md ─────────╮
│  句式 0.3  [░░░░░]                      │
│  用词 0.5  [░░░░░]                      │
│  节奏 2.0  [██░░░]                      │
│  视角 2.4  [██░░░]                      │
│ total 1.12  / 5.0                       │
│ rewrite 建议：                          │
│   1. [句式] 句长偏均；连接词起句 11 处  │
│   2. [用词] AI-slop 套话 16 处（-1.3） │
╰─────────────────────────────────────────╯
```
</details>

<h2><img src="https://api.iconify.design/tabler:terminal-2.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> 用法</h2>

```bash
wenti list                                  # 看可用文体 pack（v0.1：sanlian 三联体）
wenti score draft.md --pack sanlian --json  # JSON 报告（agent 解析用）
wenti rewrite draft.md --pack sanlian       # 按三联体 voice card + few-shots 重写
wenti score draft.md --pack sanlian --dry-run   # 离线自检，不调模型
```

`--json` 输出 `{pack, sub_scores, total, suggestions, dry_run}`，agent 直接读这个结构在会话里固定 pack id 跨篇保持文体。完整示例见 [`examples/before_after.md`](./examples/before_after.md)（同一篇草稿 bare vs 三联体，各打一次分）与 [`SKILL.md`](./SKILL.md)（agent 调用契约）。

<h2><img src="https://api.iconify.design/tabler:photo.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> Demo</h2>

![demo](assets/demo.gif)

同一篇 bare-model 草稿，三联体 pack 把总分从 **1.12 → 3.82**（lift +2.70，四个维度全抬升）。这是整个产品立场在一个文件里的可证伪证据，见 [`examples/before_after.md`](./examples/before_after.md)。

<h2><img src="https://api.iconify.design/tabler:adjustments.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> 配置</h2>

| key | 类型 | 默认 | 含义 |
|---|---|---|---|
| `WENTI_BASE_URL` | str | — | OpenAI-compatible 端点（国产模型 base_url） |
| `WENTI_API_KEY` | str | — | 上述端点的 api key |
| `WENTI_MODEL` | str | `qwen-max` | 模型名（doubao/kimi/glm 任意） |
| `--dry-run` | flag | auto | 未设 env 时自动启用本地启发式打分 |
| `--pack` | str | `sanlian` | 文体 pack id（v0.1 仅 sanlian） |

rubric 维度与权重（`wenti/scorer/rubric.yaml`，mvp_plan §2 锁定）：句式 0.3 / 用词 0.3 / 节奏 0.2 / 视角 0.2，`total = Σ(weight × sub_score)`，0-5。

<h2><img src="https://api.iconify.design/tabler:credit-card.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> 付费 / Pricing</h2>

v0.1 全部 **free + OSS**——一个三联体 pack + 本地 scorer + CLI，MIT 协议，没有付费墙。商业形态是**后续**（deliberately not v0.1）：

- **免费层**：三联体 pack + 本地 `wenti score/rewrite`，永久免费。
- **Premium 文体 pack**：南方周末体 / GQ报道体 / 新周刊体，单 pack ¥39，bundle ¥99/月（含优先上新）。
- **Hosted 风格评分 endpoint**：¥29/月/座——不用 API key、不用终端，粘贴公众号草稿即出 before/after 打分。给不碰 CLI 的 prosumer 作者与 3–5 人的自媒体工作室（连载专栏跨篇 voice 一致是日常痛点）。
- **企业 license**：给媒体机构（三联 / GQ CN）做 house-style 规模化执行。

最小"刷信用卡"路径：一个 hosted web demo（无需安装）→ 粘贴草稿看三联体打分 → paywall"想要南方周末体？¥39 解锁"。v0.1 CLI 是 OSS 证据层，hosted demo 是转化漏斗，premium pack 是第一笔收费。在 install 数清 ~500 之前不过度工程化计费。

<h2><img src="https://api.iconify.design/tabler:scale.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> 对比 vs taste-skill</h2>

| 维度 | Wenti | [taste-skill](https://github.com/Leonxlnx/taste-skill) |
|---|---|---|
| 极性 | 正向（装 named 文体） | 负向（去 slop） |
| 中文长文体 pack | ✓ 三联体 hand-curated | — |
| 风格评分 rubric（可证伪） | ✓ 句式/用词/节奏/视角 | — |
| 跨篇 series 一致 | ✓ pack id 固定 | — |
| 全球采纳规模 | —（v0.1 刚起步） | ✓ 79k star |
| 通用 anti-slop 覆盖 | partial（仅中文长文体） | ✓（跨语种通用） |

taste-skill 在**规模与通用 anti-slop 覆盖**上更好——它是 79k star 的类目领头。Wenti 不竞争通用 anti-slop，只做正向中文长文体这一窄面；护城河是 rubric + 跨篇一致，不是 few-shot 本身（few-shot 一个 PR 就能抄走）。

<h2><img src="https://api.iconify.design/tabler:map-2.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> 路线图</h2>

- [x] **m1** — 三联体 pack（voice card + few-shots）+ 风格评分 rubric + LLM-as-judge scorer + `wenti score/rewrite` CLI + before/after demo
- [ ] **m2** — 南方周末体 / GQ报道体 premium pack；跨篇 series-consistency 记忆
- [ ] **m3** — Hosted 风格评分 endpoint（无 CLI）；微信支付 + 手机号登录；2–3 design-partner 公众号实测连载
- [ ] 后续 — 企业 house-style license；自动 pack 生成（仅作内部工具，不公开——公开会消解护城河）

<h2><img src="https://api.iconify.design/tabler:license.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> License</h2>

MIT，见 [LICENSE](./LICENSE)。提 issue / PR 见 [Issues](https://github.com/SuperMarioYL/wenti/issues)。

<h2><img src="https://api.iconify.design/tabler:share.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> 分享</h2>

```
Wenti — 给 agent 装上一种可命名的中文长文体的 Skill。三联体 pack + 风格评分 rubric，把 bare-model 到三联体的差距量化成 0-5 分：1.12 → 3.82。不是 anti-slop 过滤器，是正向 taste 库。https://github.com/SuperMarioYL/wenti
```

<p align="center"><sub><a href="./LICENSE">MIT</a> © 2026 SuperMarioYL</sub></p>
