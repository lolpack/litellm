import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Final

_MODULE_PATH: Final = Path(__file__).resolve().parents[2] / "scripts" / "pyrefly_check.py"
_SPEC: Final = importlib.util.spec_from_file_location("pyrefly_check", _MODULE_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: Final = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
gate: Final[ModuleType] = _MODULE


def test_count_pyrefly_groups_only_errors() -> None:
    payload: Final = """{"errors": [
        {"name": "bad-return", "severity": "error"},
        {"name": "bad-return", "severity": "error"},
        {"name": "deprecated", "severity": "warning"}
    ]}"""

    assert gate.count_pyrefly(payload) == {"bad-return": 2}


def test_budget_breaches_reports_growth_and_new_error_kinds() -> None:
    budget: Final = gate.ErrorBudget.model_validate({"bad-return": {"limit": 2}, "bad-assignment": {"limit": 1}})
    counts: Final = {"bad-return": 3, "bad-assignment": 1, "new-check": 1}

    assert gate.budget_breaches(counts, budget) == (
        ("bad-return", 3, 2),
        ("new-check", 1, 0),
    )


def test_budget_breaches_accepts_counts_at_or_below_limits() -> None:
    budget: Final = gate.ErrorBudget.model_validate({"bad-return": {"limit": 2}, "bad-assignment": {"limit": 1}})

    assert gate.budget_breaches({"bad-return": 2}, budget) == ()


def test_ratcheted_budget_only_lowers_existing_limits() -> None:
    budget: Final = gate.ErrorBudget.model_validate(
        {"fixed": {"limit": 3}, "grew": {"limit": 2}, "cleared": {"limit": 1}}
    )

    assert gate.ratcheted_budget({"fixed": 1, "grew": 4, "new-check": 2}, budget) == {
        "cleared": {"limit": 0},
        "fixed": {"limit": 1},
        "grew": {"limit": 2},
    }


def test_vacuous_run_is_rejected_for_nonempty_baseline() -> None:
    nonempty_budget: Final = gate.ErrorBudget.model_validate({"bad-return": {"limit": 1}})
    zero_budget: Final = gate.ErrorBudget.model_validate({"bad-return": {"limit": 0}})

    assert gate.is_vacuous_run({}, nonempty_budget)
    assert not gate.is_vacuous_run({}, zero_budget)
    assert not gate.is_vacuous_run({"bad-return": 1}, nonempty_budget)
