"""wenti CLI — `wenti list|score|rewrite`.

One process, one external API call (国产模型 via base_url override), zero
microservices. A human and an agent hit the identical scoring path through
this entrypoint (see SKILL.md).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .packs import list_packs, load_pack
from .scorer import load_rubric, rewrite_draft, score_draft

app = typer.Typer(
    name="wenti",
    help="正向中文长文体 taste 库 — 三联体 pack + 风格评分 rubric。",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command("list")
def list_cmd() -> None:
    """列出可用的 文体 pack。"""
    packs = list_packs()
    table = Table(title="Wenti 文体 pack", show_header=True, header_style="bold #0071E3")
    table.add_column("name", style="bold")
    table.add_column("lineage")
    table.add_column("available", justify="center")
    table.add_column("premium", justify="center")
    for p in packs:
        avail = "[green]✓[/green]" if p.get("available") else "[red]—[/red]"
        prem = "[yellow]pro[/yellow]" if p.get("premium") else "[green]free[/green]"
        table.add_row(p["name"], p["lineage"], avail, prem)
    console.print(table)


@app.command()
def score(
    draft: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True, help="草稿 markdown 文件"),
    pack: str = typer.Option("sanlian", "--pack", "-p", help="文体 pack id"),
    dry_run: Optional[bool] = typer.Option(None, "--dry-run/--no-dry-run", help="强制本地启发式打分（不调模型）"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="模型名（默认 qwen-max 或 WENTI_MODEL）"),
    json_out: bool = typer.Option(False, "--json", help="输出 JSON 而非 rich 报告"),
) -> None:
    """对一份草稿按 文体 pack 的 rubric 打风格分。"""
    text = draft.read_text(encoding="utf-8")
    wp = load_pack(pack)
    rubric = load_rubric()
    report = score_draft(text, wp, rubric, dry_run=dry_run, model=model)

    if json_out:
        console.print_json(data=report.to_dict())
        return

    mode = "[yellow]dry-run（本地启发式，未调模型）[/yellow]" if report.dry_run else "[green]model[/green]"
    sub = Table.grid(padding=(0, 1))
    sub.add_column(style="bold #6E6E73", justify="right")
    sub.add_column()
    for dim, val in report.sub_scores.items():
        bar_len = int(val)
        bar = "█" * bar_len + "░" * (5 - bar_len)
        sub.add_row(dim, f"[bold]{val:.1f}[/bold]  [{bar}]")
    sub.add_row("total", f"[bold #0071E3]{report.total:.2f}[/bold #0071E3]  / 5.0")

    render_bits: list = [sub]
    if report.suggestions:
        render_bits.append(Text("\nrewrite 建议：", style="bold"))
        for i, s in enumerate(report.suggestions, 1):
            render_bits.append(Text(f"  {i}. [{s.dim}] {s.issue}", style="white"))
            render_bits.append(Text(f"     {s.rewrite}", style="italic #5E5CE6"))

    header = f"[bold]{wp.lineage}[/bold]  ·  模式 {mode}\n[dim]pack: {report.pack}[/dim]\n"
    console.print(
        Panel(Group(*render_bits), title=f"风格评分 · {draft.name}", border_style="#0071E3")
    )
    console.print(header)


@app.command()
def rewrite(
    draft: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True, help="草稿 markdown 文件"),
    pack: str = typer.Option("sanlian", "--pack", "-p", help="文体 pack id"),
    dry_run: Optional[bool] = typer.Option(None, "--dry-run/--no-dry-run", help="强制本地路径（不调模型）"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="模型名"),
) -> None:
    """把一份草稿按 文体 pack 重写（三联体 voiced）。"""
    text = draft.read_text(encoding="utf-8")
    wp = load_pack(pack)
    out = rewrite_draft(text, wp, dry_run=dry_run, model=model)
    console.print(Panel(out, title=f"rewrite · {wp.lineage}", border_style="#5E5CE6"))


@app.callback()
def main() -> None:
    """Wenti — 给 agent 装上一种可命名的中文长文体。"""
    return


if __name__ == "__main__":
    app()
