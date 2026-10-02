# Pyrefly and basedpyright diagnostic comparison

## Method

This report compares error-severity diagnostics by normalized repository path and one-based starting line. A shared location means both tools found at least one error on that source line. It does not imply that their rules or messages are semantically identical

The source snapshot produced 148,320 basedpyright errors at 78,369 locations and 73,588 Pyrefly errors at 55,483 locations. The tools shared 28,622 locations. Another 49,747 locations were basedpyright-only and 26,861 were Pyrefly-only

## Strong overlaps

These examples show the closest rule and message matches

| Location | basedpyright | Pyrefly | Source shape |
| --- | --- | --- | --- |
| `litellm/__init__.py:180` | `reportMissingTypeArgument` | `implicit-any-type-argument` | Bare `List` annotation |
| `litellm/__init__.py:184` | `reportExplicitAny` | `explicit-any` | Nested dictionary containing `Any` |
| `litellm/__init__.py:196` | `reportExplicitAny` | `explicit-any` | Optional dictionary containing `Any` |
| `litellm/__init__.py:206` | `reportMissingTypeArgument` | `implicit-any-type-argument` | Bare `Callable` annotation |

The aggregate comparison confirms these examples. Missing parameter annotations match on all 3,583 Pyrefly locations. Explicit `Any` matches on 1,719 of Pyrefly's 1,721 locations. Missing generic arguments match directly at 10,721 locations, although Pyrefly's broader rule also overlaps basedpyright unknown-parameter findings at 7,970 locations

## Basedpyright-only examples

These are non-unknown diagnostics with no Pyrefly error beginning on the same line

| Location | basedpyright diagnostic | What Pyrefly misses at that line |
| --- | --- | --- |
| `litellm/batches/batch_utils.py:461` | `reportArgumentType` | A string passed to a `FileContentProvider` parameter |
| `litellm/caching/caching_handler.py:357` | `reportArgumentType` | `list[str]` passed where nested integer lists are also part of the invariant type |
| `litellm/cost_calculator.py:413` | `reportReturnType` | A declared tuple return with a path that returns no value |
| `litellm/experimental_mcp_client/client.py:675` | `reportReturnType` | A possibly unbound generic result returned to the caller |
| `litellm/caching/redis_cache.py:958` | `reportAttributeAccessIssue` | `scan_iter` accessed on a client type without that attribute |
| `litellm/integrations/opentelemetry.py:1397` | `reportOptionalMemberAccess` | `set_status` called on a possibly absent parent span |
| `litellm/integrations/deepeval/deepeval.py:112` | `reportCallIssue` | Constructor call missing required parameters |
| `litellm/proxy/management_endpoints/key_management_endpoints.py:743` | `reportTypedDictNotRequiredAccess` | Direct access to a non-required TypedDict key |

The absence of a same-line Pyrefly error does not prove that Pyrefly missed the entire data flow. It can report a cause or consequence on another line. These examples still show that replacing the checker changes which edit locations developers are asked to fix

## Pyrefly-only examples

These locations have no basedpyright error beginning on the same line

| Location | Pyrefly diagnostic | What Pyrefly adds at that line |
| --- | --- | --- |
| `litellm/completion_extras/litellm_responses_transformation/transformation.py:115` | `bad-return` | A union containing `object` returned as a concrete list |
| `litellm/cost_calculator.py:2551` | `bad-return` | `object` can escape from a function declared to return `float` |
| `litellm/caching/valkey_semantic_cache.py:220` | `bad-assignment` | Bytes assigned to a query dictionary limited to strings and floats |
| `litellm/caching/redis_cache.py:1875` | `missing-attribute` | `aclose` absent from the selected Redis client type |
| `litellm/_logging.py:138` | `implicit-bool` | A mapping, tuple, or `None` used as a condition |
| `litellm/_logging.py:151` | `missing-override-decorator` | An overriding logging filter lacks `@override` |
| `litellm/__init__.py:30` | `unused-call-result` | The boolean returned by `load_dotenv` is discarded |
| `litellm/_logging.py:91` | `unnecessary-type-conversion` | `bool()` wraps an expression already inferred as boolean |

Some Pyrefly-only findings sit on lines carrying a basedpyright suppression. For example, `litellm/caching/redis_batch.py:337` has a scoped `reportArgumentType` suppression while Pyrefly reports `bad-argument-type`. This is a migration concern rather than evidence that basedpyright cannot detect the issue

## Similar names with different boundaries

Pyrefly's 9,307 `unknown-argument-type` findings share a location with 5,683 basedpyright `reportUnknownArgumentType` findings. Another 2,158 share a location with basedpyright `reportUnknownMemberType`. Pyrefly is working on explicit unknown-type support, so these differences should be remeasured when that work lands rather than treated as permanent migration work

Pyrefly's `implicit-bool` has no direct basedpyright equivalent in the enabled configuration. It often appears where basedpyright reports an upstream unknown member or variable, but it also reports fully known values such as strings and tuples used for truth testing

Pyrefly's `implicit-any-type-argument` combines at least two basedpyright concepts. It finds missing generic parameters, and it also reports generic parameters that remain unknown after inference. Budgeting it as if it were only `reportMissingTypeArgument` would hide that difference

## Reproducing the location comparison

Run both checkers with JSON output, normalize basedpyright's absolute paths relative to the repository, and group error-severity diagnostics by `(path, start_line)`. Compare the resulting key sets for shared and checker-only locations. For shared locations, compare the Cartesian product of rule names only as an investigation aid because multiple diagnostics can begin on one line
