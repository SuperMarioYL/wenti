# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-10-19

### Fixed

- **model 路径对结构漂移的 judge 返回不再崩溃**：`_model_score` 此前假定
  解析出的 JSON 是规范对象——judge 返回顶层数组/字符串、`sub_scores` 为
  字符串或 null、分值为非数字字符串、suggestions 项为字符串时，直接抛
  AttributeError/ValueError（离线 mock 复现 6 种形态）；现防御性收窄——
  非对象按空处理、非数字维度回落 2.5 中位分、非对象 suggestion 项跳过，
  v0.2.0 的 0-5 钳制不变，规范返回的行为零变化。
- **CLI 模型路径缺凭据时给出干净报错**：`wenti score|rewrite --no-dry-run`
  在未设 `WENTI_BASE_URL`/`WENTI_API_KEY` 时，此前直接抛 openai.OpenAIError
  堆栈（且提示设置 OPENAI_API_KEY，与本产品的变量名不符）；现打印一行
  可执行提示（含离线 dry-run 替代方案）并以退出码 1 结束。库的自动
  dry-run 探测与 client 注入契约不变。

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

[Unreleased]: https://github.com/SuperMarioYL/wenti/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/SuperMarioYL/wenti/releases/tag/v0.3.0
[0.2.0]: https://github.com/SuperMarioYL/wenti/releases/tag/v0.2.0
[0.1.0]: https://github.com/SuperMarioYL/wenti/releases/tag/v0.1.0
