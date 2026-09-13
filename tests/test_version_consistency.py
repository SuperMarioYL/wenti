"""Version lockstep — every shipped version surface must agree.

v0.2.0 establishes the single source of truth: pyproject.toml,
wenti/__version__, SKILL.md frontmatter and the newest CHANGELOG section
must all carry the same version, and `wenti --version` must print it.
Everything here is a file read or an in-process CLI invocation — no
shelling out to binaries a GH runner may lack.
"""

from __future__ import annotations

import re
from pathlib import Path

from typer.testing import CliRunner

from wenti import __version__
from wenti.cli import app

REPO = Path(__file__).resolve().parent.parent
RELEASES = "https://github.com/SuperMarioYL/wenti/releases/tag"

runner = CliRunner()


def _pyproject_version() -> str:
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    assert m, "pyproject.toml is missing a [project] version"
    return m.group(1)


def _skill_version() -> str:
    text = (REPO / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^version:\s*([0-9][0-9.]*)\s*$", text, re.M)
    assert m, "SKILL.md frontmatter is missing version"
    return m.group(1)


def _changelog_versions() -> list[str]:
    text = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    return re.findall(r"^## \[([0-9][0-9.]*)\]", text, re.M)


def test_version_surfaces_agree():
    assert _pyproject_version() == __version__, "pyproject.toml drifted"
    assert _skill_version() == __version__, "SKILL.md frontmatter drifted"
    versions = _changelog_versions()
    assert versions, "CHANGELOG.md has no versioned sections"
    assert versions[0] == __version__, (
        f"CHANGELOG newest section {versions[0]!r} != shipped {__version__!r}"
    )


def test_changelog_link_refs_are_defined():
    text = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    for v in _changelog_versions():
        assert f"[{v}]: {RELEASES}/v{v}" in text, f"CHANGELOG missing ref [{v}]"
    unreleased = re.search(r"^\[Unreleased\]:\s*(\S+)", text, re.M)
    assert unreleased, "CHANGELOG missing [Unreleased] link ref"
    assert unreleased.group(1).endswith(f"v{__version__}...HEAD"), (
        f"[Unreleased] must compare against v{__version__}...HEAD, "
        f"got {unreleased.group(1)}"
    )


def test_cli_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"wenti, version {__version__}" in result.output
