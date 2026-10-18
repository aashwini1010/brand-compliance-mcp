"""The examples printed in docs/plugin-guide.md must really work.

If you change an example in the guide, change it here too (and the other way round).
"""

import csv
import json
from pathlib import Path

from brand_compliance.core.contracts import RuleExtractor, SourceAdapter
from brand_compliance.core.errors import ParseFailedError
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.core.settings import PathSettings, Settings
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.models.guide import GuideDocument, GuideNode, NodeKind
from brand_compliance.models.report import CheckResult, RunResult, RunStatus
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.models.source import SourceSpan
from brand_compliance.pipeline.bootstrap import build_registry
from brand_compliance.pipeline.orchestrator import Orchestrator
from brand_compliance.plugins.extractors import register_extractors
from brand_compliance.rules.interpret import interpret_guide
from brand_compliance.rules.vocabulary import load_vocabulary


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


def test_a_new_guide_format_needs_only_a_reader(tmp_path: Path) -> None:
    source = tmp_path / "brand.json"
    source.write_text(
        json.dumps({"colors": {"--ink": "#111111", "--paper": "#FAF7F2"}})
    )
    registry = PluginRegistry()
    registry.register(JsonTokenAdapter())
    register_extractors(registry)  # the existing finders are reused unchanged
    adapter = registry.find(SourceAdapter, lambda a: a.can_handle(source))
    rules = interpret_guide(
        adapter.load(source), registry.plugins(RuleExtractor), load_vocabulary()
    ).rules
    assert [(r.category, r.property, r.value) for r in rules] == [
        ("color_token", "--ink", "#111111"),
        ("color_token", "--paper", "#faf7f2"),
    ]
    assert all(r.status is RuleStatus.PENDING for r in rules)


def test_a_bad_json_guide_is_a_typed_parse_error(tmp_path: Path) -> None:
    source = tmp_path / "brand.json"
    source.write_text("{not json")
    try:
        JsonTokenAdapter().load(source)
    except ParseFailedError as exc:
        assert "not valid JSON" in str(exc)
    else:
        raise AssertionError("expected ParseFailedError")


def _orchestrator(workspace: Path) -> Orchestrator:
    settings = Settings(
        paths=PathSettings(
            allowed_input_dirs=[str(workspace)],
            allowed_output_dirs=[str(workspace / "out")],
        )
    )
    vocabulary = load_vocabulary()
    registry = build_registry(settings, vocabulary)
    registry.register(NoNewScriptsVerifier())
    registry.register(CsvChangesReporter())
    return Orchestrator(registry, settings, vocabulary)


def test_a_new_verifier_runs_without_touching_the_orchestrator(workspace: Path) -> None:
    summary = _orchestrator(workspace).run(
        workspace / "guide.md", workspace / "page.html", workspace / "out"
    )
    assert summary.checks["no-new-scripts"] is True
    assert summary.status is RunStatus.COMPLETED


def test_a_new_reporter_writes_its_file_into_the_run_folder(workspace: Path) -> None:
    summary = _orchestrator(workspace).run(
        workspace / "guide.md", workspace / "page.html", workspace / "out"
    )
    with Path(summary.files["changes.csv"]).open(encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["change", "rule", "element", "property", "before", "after"]
    assert len(rows) == summary.change_count + 1
