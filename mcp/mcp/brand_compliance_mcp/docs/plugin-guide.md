# Plugin guide: extending the tool without rewriting it

Everything that can grow is a plugin: an object with a `name` that satisfies one small interface from
`src/brand_compliance/core/contracts.py`. The orchestrator finds plugins through the registry and never
branches on a format name, so adding a capability is **adding one file and registering it**.

| To add… | Implement | Register in | What else changes |
|---|---|---|---|
| A guide format (PDF, JSON, URL…) | `SourceAdapter` | `plugins/sources/__init__.py` | Nothing: existing rule finders read the common tree |
| A kind of rule to find | `RuleExtractor` | `plugins/extractors/__init__.py` | Teach the meaning in `rules/normalize.py` and the wording in `config/vocabulary.toml` |
| An artifact type | `ArtifactHandler` + `StyleWriter` | `plugins/artifacts/__init__.py`, `plugins/writers/__init__.py` | A support table like `config/email_support.toml` if the medium has limits |
| A way to change an element | `RuleApplier` | `plugins/appliers/__init__.py` | Nothing else |
| A check | `Verifier` | `plugins/verifiers/__init__.py` | Nothing: it runs automatically |
| A report format | `Reporter` | `plugins/reporters/__init__.py` | Nothing: its file appears in every run folder |

External packages can register plugins without editing this repository; see [Shipping a plugin](#shipping-a-plugin-as-a-separate-package).

## The rules every plugin follows

1. **Never guess.** If you cannot be sure, say so: raise a typed error (`core/errors.py`), return a `Skip` with a
   reason, or let the normalizer mark the rule `could_not_interpret`. A plausible default is a bug.
2. **Keep the source line.** Every guide-side node and candidate carries a `SourceSpan`; reports point back to it.
3. **Never log guide or artifact content.** Log ids, counts and rule ids only; use `logging.getLogger(__name__)`.
4. **Do not edit the original.** Work on the copy you are given. Appliers *plan*; only writers change the tree.
5. **Plugins do not import from `pipeline/` or `server/`.** Use `core/`, `models/` and (for helpers) other plugins.
6. **Test it:** a unit test next to the mirrored path in `tests/unit/`, with shared fixtures only in `tests/conftest.py`.

## Example 1: a new guide format (JSON tokens)

The trick is to **present the new format in the same shape** the existing finders already read. Here a JSON file of
colours becomes a `Token | Hex` table, so the existing token-table finder, normalizer, appliers, verifiers and
reporters work unchanged.

```python
import json
from pathlib import Path

from brand_compliance.core.errors import ParseFailedError
from brand_compliance.models.guide import GuideDocument, GuideNode, NodeKind
from brand_compliance.models.source import SourceSpan


class JsonTokenAdapter:
    """Reads {"colors": {"--ink": "#111111"}} and presents it as a Token/Hex table."""

    name = "json-tokens"

    def can_handle(self, source: Path) -> bool:
        return source.suffix.lower() == ".json"

    def load(self, source: Path) -> GuideDocument:
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ParseFailedError(f"{source.name} is not valid JSON: {exc}") from exc
        colors = data.get("colors", {})
        span = SourceSpan(file=source.name, line_start=1, heading_path=("Colors",))
        table = GuideNode(
            kind=NodeKind.TABLE,
            span=span,
            header=["Token", "Hex"],
            rows=[[name, value] for name, value in colors.items()],
            row_lines=[1] * len(colors),  # JSON has no lines: point at the file
        )
        return GuideDocument(
            source_name=source.name, source_format="json-tokens", nodes=[table]
        )
```

Register it with one line in `plugins/sources/__init__.py`:

```python
registry.register(JsonTokenAdapter())
```

Guidelines for readers: check type, size and encoding (see `plugins/sources/base.py`); keep page or line numbers
in the spans; for PDF, give table rows their page; for URLs, fetching must be off by default and must block
private addresses. A reader never decides what a rule *means*; that is the normalizer's job.

## Example 2: a new check (a `Verifier`)

A verifier looks at the original and the output and returns a `CheckResult`. It declares a `scope`:

- `"output"` (the default): judges the **written** file; a failure withholds `branded.html`.
- `"changes"`: judges the **plan** before writing. It may name the changes to undo through
  `failed_change_ids` and `change_reasons`; the verification loop then undoes them and checks again.

```python
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule


class NoNewScriptsVerifier:
    """Fails if the output has more <script> elements than the original."""

    name = "no-new-scripts"
    scope = "output"  # judges the written file ("changes" would judge the plan)

    def check(
        self,
        original: ArtifactModel,
        output: ArtifactModel,
        rules: list[Rule],
        changes: list[Change],
    ) -> CheckResult:
        before = len(original.tree.xpath("//script"))
        after = len(output.tree.xpath("//script"))
        return CheckResult(
            name=self.name,
            passed=after <= before,
            details=[f"{before} script(s) before, {after} after"],
        )
```

Register it in `plugins/verifiers/__init__.py` (or from an external package). It appears in the run summary's
`checks` and in `report.md` automatically. Two cautions: `original` is a pristine parse, `output` is the edited
copy; and a check that only repeats another check's logic proves little, so prefer an independent measurement.

## Example 3: a new report format (a `Reporter`)

A reporter declares the `filename` it writes, so every report can list all files of the run (itself included).

```python
import csv
from pathlib import Path

from brand_compliance.models.report import RunResult


class CsvChangesReporter:
    """Writes every change as one CSV row."""

    name = "csv-changes"
    format = "csv"
    filename = "changes.csv"

    def render(self, result: RunResult, output_dir: Path) -> Path:
        path = output_dir / self.filename
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["change", "rule", "element", "property", "before", "after"]
            )
            for c in result.changes:
                writer.writerow(
                    [c.id, c.rule_id, c.location, c.property, c.before or "", c.after]
                )
        return path
```

## The other plugin kinds, briefly

**`RuleExtractor`**: `extract(document) -> list[RuleCandidate]`. Only *find* things and record the exact span in
`hints` (a `kind` plus string fields). Meaning and status are decided in `rules/normalize.py`, which is where a
new candidate `kind` gets a handler. Claimed lines are tracked automatically: whatever no finder claims is kept as
"could not interpret", so nothing is lost.

**`RuleApplier`**: `plan(rule, artifact) -> ApplyResult` (`changes`, `skipped`, `satisfied`). Most appliers just
subclass `RoleStyleApplier` and set `name` and `categories`; role matching (dotted roles, aliases), light/dark
scope, "already matches" and inline-style handling are done for you. Never mutate the tree here: return `Change`
records (element path, property, before, after). If you cannot apply a value, return a `Skip` with a human reason.

**`ArtifactHandler` + `StyleWriter`**: subclass `HtmlArtifactHandler` for another HTML-like medium (set `name`,
`artifact_type`, and override `extra_notes`), then write a `StyleWriter` for that type. The writer must keep
everything except the edits (comments, doctype, scripts), recognise its own earlier output so a re-run is
identical, and add only what it must. Add `ArtifactType` to `models/artifact.py` and teach the classifier its
signals. For a medium with limits, follow `config/email_support.toml` + `plugins/appliers/support.py`: unsupported
values become reported skips, never approximations.

## Shipping a plugin as a separate package

Expose a zero-argument callable (a class works) under the entry-point group `brand_compliance.plugins`:

```toml
# in the other package's pyproject.toml
[project.entry-points."brand_compliance.plugins"]
json_tokens = "my_package.adapters:JsonTokenAdapter"
```

When that package is installed, `build_registry()` loads it. A plugin that fails to import, is not a valid
plugin, or reuses a name is **logged and skipped**; it never stops the server. To *replace* a built-in, call
`registry.register(plugin, replace=True)`; `registry.unregister(kind, name)` removes one.

## Checklist before you open a pull request

- [ ] Implements exactly one interface and has a unique `name` (and `filename` for reporters)
- [ ] Raises typed errors or returns reasons; no guessing, no silent fallbacks
- [ ] No content in logs; spans kept; original untouched
- [ ] Unit tests cover success **and** failure; coverage stays ≥ 80%
- [ ] `ruff check .`, `ruff format .`, `mypy` and `pytest` are clean
- [ ] If it changes outcomes on the sample guide or artifacts, run the evaluation
      (`PYTHONPATH=src python -m brand_compliance.evaluation`) and explain any case that changes
- [ ] `docs/DEVELOPMENT-GUIDE.md` updated (its maintenance checklist lists what to touch)

The examples above are exercised by `tests/unit/plugins/test_documented_examples.py`, so this guide is kept honest by the build.
