# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-11-23

### Fixed

- **注入的 client 现在真正走模型路径**：`score_draft` / `rewrite_draft`
  此前只按 `WENTI_BASE_URL` / `WENTI_API_KEY` 判断 dry-run——调用方显式
  `client=...`（或 `base_url` + `api_key` 参数）时，环境变量未设仍会静默
  落回本地启发式（复现：judge 给 4.4/4.5/4.6/4.7，返回的却是
  1.5/1.5/2.0/0.5 且 `dry_run=True`）。现由 `resolve_dry_run` 统一裁决：
  显式 `dry_run` 优先，其次 CLI 无变化，client 或显式凭据选模型路径，
  最后才是环境变量兜底。`rewrite_draft` 同样生效。
- **judge 返回不含可解析 JSON 时不再抛栈，也不再静默冒充分数**：
  `_extract_json` 现在逐个 `{` 起点解析（`raw_decode`），围栏后带花括号
  说明文字也能取出真正的对象；完全无可解析 JSON 时返回空对象，
  `ScoreReport` 新增 `warnings` 字段点名哪些维度回落 2.5 中位分，CLI 打印
  该提示，`--json` 输出也携带——分数不再被当作"量出来的结论"。
- **未知 / 未随包发布的 `--pack` 不再输出 FileNotFoundError 堆栈**：
  `wenti score|rewrite --pack <typo|nanfangzhoumo>` 此前直接抛
  FileNotFoundError（终端显示堆栈、泄漏安装路径）；现在打印请求的 id、
  可用 pack（sanlian）与 premium 未随包发布的说明，并以退出码 1 结束。
- **dry-run rewrite 原样返回草稿**：`rewrite_draft` 此前会在返回文本前
  拼接 `# [wenti dry-run] ...` 横幅，与 SKILL.md 承诺的"原稿"矛盾，
  也污染被重定向保存的草稿；现在库原样返回，提示改由 CLI 在面板外打印。

### Added

- `ScoreReport.warnings`（wenti/packs/schema.yaml 记录为可选字段）：
  模型路径的诚实提示，`to_dict()` 与 `--json` 均包含。
- `wenti.scorer.resolve_dry_run`：dry-run / 模型路径的单一裁决点，CLI 复用。
- 版本一致性测试新增站点面：`web/site.json` 的 `meta.content_version`
  与 footer 版本标识必须与包版本一致。

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

[Unreleased]: https://github.com/SuperMarioYL/wenti/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/SuperMarioYL/wenti/releases/tag/v0.4.0
[0.3.0]: https://github.com/SuperMarioYL/wenti/releases/tag/v0.3.0
[0.2.0]: https://github.com/SuperMarioYL/wenti/releases/tag/v0.2.0
[0.1.0]: https://github.com/SuperMarioYL/wenti/releases/tag/v0.1.0
