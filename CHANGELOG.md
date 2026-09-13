# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-09-14

### Fixed

- **dry-run rewrite 建议现在指向真正最弱的两个维度**：`_heuristic_suggestions`
  此前固定取 rubric 顺序的前两个维度（句式/用词），与 docstring 及
  `examples/before_after.md` 宣称的"两个最弱维度"不符（例如三联体 demo 稿的
  节奏 2.6 低于 用词 4.5，却从未被建议）；现按 sub_score 升序取最低两个，
  同分时保持 rubric 顺序（确定性）。
- **model 路径的 sub_scores 现被钳制到 0-5**：`_model_score` 此前直接
  round 模型返回值，judge 把刻度读成 0-10 时总分可超过 5.0（复现得到
  8.47），违反 `wenti/packs/schema.yaml` 的 ScoreReport 0-5 契约；现与
  dry-run 路径共用 `_clamp`，两条路径同一把尺子。
- **`_extract_json` 容忍 fenced JSON 后跟说明文字**：此前 ``` 围栏后带任何
  尾随文字时 brace-block 回退不可达，直接抛 `JSONDecodeError`；现先尝试
  直接解析、失败再回退到首个 `{...}` 块。

### Added

- `wenti --version`：从 `wenti.__version__` 单一来源打印版本。
- `CHANGELOG.md`（本文件）与 `tests/test_version_consistency.py`：pyproject
  版本、`wenti.__version__`、SKILL.md 版本、CHANGELOG 最新条目四处在测试中
  锁定一致。
- `web/site.json` 携带 `meta.content_version` 与页脚版本标识。

## [0.1.0] - 2026-08-23

### Added

- 三联生活周刊体 文体 pack（voice card + hand-curated few-shots）。
- 风格评分 rubric（句式/用词/节奏/视角，0-5，权重 0.3/0.3/0.2/0.2）。
- LLM-as-judge scorer（qwen/doubao/kimi/glm via base_url）+ 离线 dry-run
  启发式路径。
- `wenti list|score|rewrite` CLI（typer + rich）。
- `SKILL.md` agent 调用契约与 `examples/before_after.md` before/after demo。

[Unreleased]: https://github.com/SuperMarioYL/wenti/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/SuperMarioYL/wenti/releases/tag/v0.2.0
[0.1.0]: https://github.com/SuperMarioYL/wenti/releases/tag/v0.1.0
