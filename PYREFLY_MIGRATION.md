# Pyrefly migration assessment

## Scope

The comparison uses Python 3.12.13, basedpyright 1.39.7, and Pyrefly 1.3.1 on the same checkout and development environment. Both tools checked the 2,778 modules selected by their configurations. Pyrefly uses its `all` preset rather than `strict` because `strict` omits its unknown-type checks. The `all` preset enables every implemented Pyrefly diagnostic, including checks that have no basedpyright equivalent

The commands ran once after dependency installation, with output redirected to files so terminal rendering did not dominate either result

```bash
TIMEFORMAT='real=%R user=%U sys=%S'
time NODE_OPTIONS=--max-old-space-size=8192 uv run --no-sync basedpyright --outputjson > /tmp/basedpyright-baseline.json
time uv run --no-sync pyrefly check --output-format json --summary=full --progress-bar no > /tmp/pyrefly-baseline.json
```

## Timing and totals

| Checker | Wall time | Checker-reported time | Errors | Error locations | Peak memory |
| --- | ---: | ---: | ---: | ---: | ---: |
| basedpyright | 213.290s | 198.406s | 148,320 | 78,369 | Not reported |
| Pyrefly `all` | 18.794s | 18.46s | 73,588 | 55,483 | 821.5 MiB |

Pyrefly was 11.3 times faster by wall time in this run. The totals are not a measure of equivalent coverage because the tools implement and group checks differently. They reported at least one error on the same file and line at 28,622 locations, which is 36.5% of basedpyright's error locations and 51.6% of Pyrefly's. The longer [diagnostic comparison](PYREFLY_DIAGNOSTIC_COMPARISON.md) records concrete shared and checker-only lines

## Comparable errors

The strongest one-to-one matches have nearly identical totals or occur on the same source lines

| basedpyright | Count | Pyrefly | Count | Same-line matches |
| --- | ---: | --- | ---: | ---: |
| `reportMissingTypeArgument` | 10,742 | `implicit-any-type-argument` | 19,812 | 10,721 |
| `reportMissingParameterType` | 3,587 | `implicit-any-parameter` | 3,583 | 3,583 |
| `reportExplicitAny` | 1,727 | `explicit-any` | 1,721 | 1,719 |
| `reportArgumentType` | 1,727 | `bad-argument-type` | 1,513 | 1,077 |
| `reportAssignmentType` | 275 | `bad-assignment` | 266 | 142 |
| `reportAttributeAccessIssue` | 451 | `missing-attribute` | 265 | 162 |
| `reportReturnType` | 173 | `bad-return` | 158 | 124 |
| `reportDeprecated` | 208 | `deprecated` | 146 | 132 |
| `reportUnnecessaryCast` | 108 | `redundant-cast` | 111 | 90 |

`implicit-any-type-argument` is broader than `reportMissingTypeArgument`. At the same lines it also overlaps 7,970 `reportUnknownParameterType` findings, so its higher total does not mean Pyrefly finds twice as many missing generic annotations

## Coverage differences

Pyrefly is actively adding explicit unknown-type support, so unknown diagnostics are excluded from the high-level migration estimate. Removing basedpyright's 117,630 unknown argument, member, variable, and parameter findings leaves 30,690 errors. Removing Pyrefly's 11,056 explicitly named unknown argument, variable, and attribute findings leaves 62,532 errors. These adjusted totals still are not directly equivalent because Pyrefly reports additional rule families

Basedpyright's 6,901 `reportAny` findings remain a coverage difference outside that exclusion. They cover uses of `Any` across expressions. Pyrefly splits out 513 implicit and 194 explicit `Any` returns, but it does not provide an equivalent general-use diagnostic

Pyrefly also finds classes of errors that the basedpyright configuration does not. Its largest additions are 22,949 `implicit-bool`, 3,699 `unannotated-return`, 2,241 `missing-override-decorator`, 1,577 `unused-call-result`, 689 `implicit-reexport`, and 266 `implicitly-defined-attribute` findings. These account for 31,421 errors and explain why comparing only total errors would overstate parity

Some names are similar without being equivalent. Pyrefly's 9,307 unknown arguments share a line with 5,683 basedpyright unknown-argument findings, but another 2,158 occur where basedpyright reports an unknown member. Likewise, Pyrefly's implicit-boolean check often reports where basedpyright instead reports an unknown member or variable. Migration work must review representative diagnostics rather than mechanically translating rule names

## Migration plan

Pyrefly cannot currently replace the existing basedpyright gate with equivalent coverage. Unknown-type parity should be reassessed after Pyrefly's in-progress support lands. The remaining blockers include general `Any` propagation, different correctness findings, suppression syntax, and the repository's budget and baseline workflow

The Pyrefly gate uses `pyrefly-code-budget.json` as a per-error-kind baseline. Existing findings pass, any increase above a kind's limit fails, and a new error kind has a zero limit. `make lint-pyrefly-budget-update` only lowers existing limits after cleanup, while `make lint-pyrefly` makes the gate available to development and CI. This follows the repository's per-rule budget model without committing Pyrefly's much larger line-by-line native baseline

Keep basedpyright as the required checker while reducing the Pyrefly budget in this order: shared correctness findings, Pyrefly-only correctness findings, missing annotations, override decorators, and style-oriented findings such as unused call results. Fix shared defects in code and report reduced or incorrect diagnostics upstream instead of weakening both configurations

The `litellm` package contains 569 `# pyright: ignore[...]` suppressions. During dual checking, keep checker-specific suppressions narrow and include exact error codes and reasons. Update suppression validation and contributor guidance before accepting Pyrefly directives in production code

Reassess unknown-type coverage when Pyrefly's explicit unknown-type work is released. A final cutover also requires equivalent general `Any` checks, a zero Pyrefly budget, editor integration, a stable type-check environment with generated Prisma imports, and coverage for the separately checked `tests/e2e` tree. The current count budget does not yet perform based-branch comparisons or publish cached base artifacts like `scripts/type_check_gate.py`; those are required before Pyrefly can become the sole gate
