#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, RootModel

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
BUDGET_PATH: Final = REPO_ROOT / "pyrefly-code-budget.json"
DEFAULT_LIMIT: Final = 0


class PyreflyDiagnostic(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    severity: str


class PyreflyOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    errors: tuple[PyreflyDiagnostic, ...]


class BudgetEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int


class ErrorBudget(RootModel[dict[str, BudgetEntry]]):
    pass


def count_pyrefly(payload: str) -> dict[str, int]:
    parsed: Final = PyreflyOutput.model_validate_json(payload)
    return dict(Counter(error.name for error in parsed.errors if error.severity == "error"))


def budget_breaches(counts: dict[str, int], budget: ErrorBudget) -> tuple[tuple[str, int, int], ...]:
    return tuple(
        (name, count, budget.root.get(name, BudgetEntry(limit=DEFAULT_LIMIT)).limit)
        for name, count in sorted(counts.items())
        if count > budget.root.get(name, BudgetEntry(limit=DEFAULT_LIMIT)).limit
    )


def is_vacuous_run(counts: dict[str, int], budget: ErrorBudget) -> bool:
    return not counts and any(entry.limit for entry in budget.root.values())


def run_pyrefly() -> str:
    process: Final = subprocess.run(
        [
            str(REPO_ROOT / ".venv" / "bin" / "pyrefly"),
            "check",
            "--output-format",
            "json",
            "--summary=none",
            "--progress-bar",
            "no",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if process.returncode not in (0, 1):
        raise SystemExit(process.stderr or f"pyrefly exited {process.returncode}")
    return process.stdout


def ratcheted_budget(counts: dict[str, int], budget: ErrorBudget) -> dict[str, dict[str, int]]:
    return {name: {"limit": min(entry.limit, counts.get(name, 0))} for name, entry in sorted(budget.root.items())}


def write_budget(counts: dict[str, int], budget: ErrorBudget) -> None:
    BUDGET_PATH.write_text(f"{json.dumps(ratcheted_budget(counts, budget), indent=2)}\n")


def main() -> None:
    parser: Final = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true")
    args: Final = parser.parse_args()
    counts: Final = count_pyrefly(run_pyrefly())
    budget: Final = ErrorBudget.model_validate_json(BUDGET_PATH.read_text())
    if is_vacuous_run(counts, budget):
        raise SystemExit("Pyrefly returned no errors for a nonempty budget")
    if args.update:
        write_budget(counts, budget)
        sys.stdout.write(f"Ratcheted {BUDGET_PATH.name} against {sum(counts.values())} errors\n")
        return
    breaches: Final = budget_breaches(counts, budget)
    if not breaches:
        sys.stdout.write(f"OK: every Pyrefly error kind is within budget ({sum(counts.values())} errors total)\n")
        return
    sys.stdout.write("FAIL: Pyrefly errors exceed their limits:\n")
    for name, count, limit in breaches:
        sys.stdout.write(f"  {name}: {count} errors, limit {limit}\n")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
