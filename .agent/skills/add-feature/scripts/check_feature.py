#!/usr/bin/env python3
"""Sanity-check a Gherkin .feature file.

Checks performed:
  1. Valid Gherkin syntax.
  2. No duplicate Scenario/Scenario Outline names within the file.
  3. Every @tag used is a registered pytest marker (see pyproject.toml's
     [tool.pytest.ini_options] markers list) - an unregistered tag is
     usually a typo rather than an intentional new test tier.

Usage:
    uv run python check_feature.py path/to/some.feature
"""

import sys
import tomllib
from pathlib import Path

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser


def find_pyproject(start: Path) -> Path | None:
    for directory in [start.parent, *start.parent.parents]:
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None


def registered_markers(pyproject_path: Path | None) -> set[str]:
    if pyproject_path is None:
        return set()
    data = tomllib.loads(pyproject_path.read_text())
    markers = data.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("markers", [])
    return {entry.split(":", 1)[0].strip() for entry in markers}


def collect_scenarios_and_tags(feature: dict) -> tuple[list[tuple[str, int]], set[str]]:
    scenarios: list[tuple[str, int]] = []
    tags = {tag["name"] for tag in feature.get("tags", [])}

    for child in feature.get("children", []):
        scenario = child.get("scenario")
        if scenario is None:
            continue
        scenarios.append((scenario["name"], scenario["location"]["line"]))
        tags.update(tag["name"] for tag in scenario.get("tags", []))

    return scenarios, tags


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_feature.py path/to/some.feature", file=sys.stderr)
        return 2

    feature_path = Path(sys.argv[1])
    text = feature_path.read_text()

    ok = True

    try:
        document = Parser().parse(text)
    except CompositeParserException as exc:
        ok = False
        print(f"SYNTAX ERROR in {feature_path}:")
        for sub_error in exc.errors:
            print(f"  {sub_error}")
        print()
        print("FAILED: fix syntax errors before continuing.")
        return 1

    scenarios, tags = collect_scenarios_and_tags(document["feature"])

    seen: dict[str, int] = {}
    duplicates: list[tuple[str, int, int]] = []
    for name, line in scenarios:
        if name in seen:
            duplicates.append((name, seen[name], line))
        else:
            seen[name] = line

    if duplicates:
        ok = False
        print("DUPLICATE SCENARIO NAMES:")
        for name, first_line, dup_line in duplicates:
            print(f"  {name!r}: first defined at line {first_line}, repeated at line {dup_line}")
        print()

    markers = registered_markers(find_pyproject(feature_path))
    unregistered = {tag for tag in tags if tag.lstrip("@") not in markers}
    if unregistered:
        ok = False
        print("UNREGISTERED TAGS (not in pyproject.toml's markers list):")
        for tag in sorted(unregistered):
            print(f"  {tag}")
        print("  Registered markers:", ", ".join(sorted(markers)) or "(none)")
        print()

    if ok:
        tag_summary = ", ".join(sorted(tags)) or "none"
        print(f"OK: {feature_path} ({len(scenarios)} scenario(s), tags: {tag_summary})")
        return 0

    print("FAILED: fix the issues above before continuing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
