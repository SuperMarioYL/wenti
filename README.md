[English](./README.en.md) · [Website](https://wenti.lei6393.com) · [GitHub](https://github.com/SuperMarioYL/wenti)

<picture>
  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="./assets/presentation/hero-mobile-dark.svg">
  <source media="(max-width: 600px)" srcset="./assets/presentation/hero-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="./assets/presentation/hero-dark.svg">
  <img src="./assets/presentation/hero-light.svg" width="960" alt="Hero diagram">
</picture>

# wenti

**让不同草稿使用同一套编辑反馈标准。**

Wenti 将编辑视角卡、示例与四维评分标准打包，用于中文长文。它提供本地启发式评分，以及可选模型评分或重写。

## 为什么需要它

反复重述偏好文风会让草稿难以比较。命名 pack 与明确标准便于作者重复使用同一组条件，同时保留编辑判断。

- **复用命名标准** — 每篇草稿可选择相同 pack。
- **检查评分标准** — 维度权重与本地规则均有源码。
- **无需模型运行** — 明确 dry-run 让评分留在本地。

## 架构

<picture>
  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="./assets/presentation/architecture-mobile-dark.svg">
  <source media="(max-width: 600px)" srcset="./assets/presentation/architecture-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="./assets/presentation/architecture-dark.svg">
  <img src="./assets/presentation/architecture-light.svg" width="960" alt="Architecture diagram">
</picture>

pack 加载器读取视角卡元数据与示例。score_draft 选择明确 dry-run 启发式或已配置模型路径；四个分项按权重合成并附建议。rewrite 使用独立路径应用选定 pack。

| 组件 | 职责 |
| --- | --- |
| `Editorial pack` | wenti/packs |
| `Draft text` | User-authored input |
| `Rubric scorer` | wenti/scorer/score.py |
| `Score / suggestions` | Four dimensions and total |

## 安装与快速上手

使用仓库清单指定的运行时版本构建，并在仓库根目录运行示例。

```bash
git clone https://github.com/SuperMarioYL/wenti.git
cd wenti
uv venv .venv
uv pip install --python .venv/bin/python -e .
source .venv/bin/activate
```

示例包含原创中文场景，并以 dry_run=True 运行 score_draft，不使用凭据或网络。

```bash
.venv/bin/python examples/presentation-demo.py
```

## 实际运行示例

<picture>
  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="./assets/presentation/process-mobile-dark.svg">
  <source media="(max-width: 600px)" srcset="./assets/presentation/process-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="./assets/presentation/process-dark.svg">
  <img src="./assets/presentation/process-light.svg" width="960" alt="Process diagram">
</picture>

The recorded score is a deterministic heuristic result for the supplied text.

```text
{
  "input": "清晨，菜市场的灯还亮着。老周把白菜码在摊位上，水汽从叶脉间慢慢散开。\n\n街道醒了。\n\n他为什么还留在这里？女儿的信压在棋盘下面，时间在纸角留下浅浅的褶皱。",
  "pack": "sanlian",
  "dry_run": true,
  "sub_scores": {
    "句式": 2.0,
    "用词": 4.1,
    "节奏": 2.5,
    "视角": 2.5
  },
  "total": 2.83
}
```

完整命令与输出保存在 [docs/demo-results.json](./docs/demo-results.json). 输入和复现代码均随仓提供。

![已有终端录制](./assets/demo.gif)

保留已有录制供参考；上方文字示例给出当前可复现的操作。

## 用法

CLI 提供以下操作。示例之外的命令需要替换成你的文件路径或标识。

```bash
wenti list
wenti score draft.md --pack sanlian --dry-run --json
# Model-backed rewrite uses the configured endpoint:
wenti rewrite draft.md --pack sanlian
```

## 配置

WENTI_BASE_URL 与 WENTI_API_KEY 启用模型路径，WENTI_MODEL 指定模型。即使已有凭据，--dry-run 也强制本地评分。rubric.yaml 中句式和用词各占 0.3，节奏和视角各占 0.2。

## 集成与职责分工

<picture>
  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="./assets/presentation/integrations-mobile-dark.svg">
  <source media="(max-width: 600px)" srcset="./assets/presentation/integrations-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="./assets/presentation/integrations-dark.svg">
  <img src="./assets/presentation/integrations-light.svg" width="960" alt="Integrations diagram">
</picture>

以下路径已有源码实现。按任务选择输入，并把生成的结果与项目一起保存。

| 路径 | 已实现职责 |
| --- | --- |
| Chinese draft | Local text input |
| sanlian pack | Bundled project editorial profile |
| Local heuristics | Explicit --dry-run route |
| Compatible model API | Optional scoring / rewriting |

## 限制与后续方向

- 启发式奖励特定用词和句段特征；分数不是客观写作质量，也不是独立编辑评估。
- 随仓 sanlian 名称指项目 pack，不表示刊物背书。
- 离线示例只为原创短 fixture 评分，不展示模型重写或读者效果提升。

更多 pack 和跨草稿一致性工具属于后续工作。新标准应结合独立编辑反馈评估，而不只看自身示例。

## 许可与贡献

许可见 [LICENSE](./LICENSE). 反馈问题时请提供最小输入、执行命令和实际输出。
