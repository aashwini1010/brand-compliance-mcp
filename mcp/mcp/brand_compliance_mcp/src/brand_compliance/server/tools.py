"""The MCP tools. Each one validates, delegates to the orchestrator, maps errors."""

import logging
from collections import Counter
from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.models.artifact import ArtifactType, Classification
from brand_compliance.models.report import RunSummary
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.pipeline.orchestrator import Orchestrator
from brand_compliance.server.error_mapping import guarded
from brand_compliance.server.schemas import (
    ExtractedRules,
    PluginList,
    ReportText,
    RuleView,
)

logger = logging.getLogger(__name__)

MAX_RULES_RETURNED = 1000
_READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}
_WRITES_FILES = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "openWorldHint": False,
}

GuidePath = Annotated[
    str, Field(description="Path to the brand guide on the server's machine")
]
ArtifactPath = Annotated[
    str, Field(description="Path to the HTML file on the server's machine")
]


def _view(rule: Rule) -> RuleView:
    return RuleView(
        id=rule.id,
        status=rule.status.value,
        category=rule.category,
        role=rule.target_role,
        property=rule.property,
        value=rule.value,
        scope=rule.scope.value,
        severity=rule.severity.value,
        guide_line=rule.source_span.describe(),
        heading=" > ".join(rule.source_span.heading_path),
        reason=rule.reason,
        notes=rule.notes,
    )


def register_tools(
    mcp: FastMCP, orchestrator: Orchestrator, registry: PluginRegistry
) -> None:
    """Add every tool and resource to the server."""

    @mcp.tool(name="apply_brand", annotations=_WRITES_FILES)
    @guarded("apply_brand")
    def apply_brand(
        guide_path: GuidePath,
        artifact_path: ArtifactPath,
        output_dir: Annotated[
            str,
            Field(
                description="Folder for the new run folder (an allowed output folder)"
            ),
        ] = "output",
        artifact_type: Annotated[
            Literal["static", "email"] | None,
            Field(description="Force the artifact type; omit to detect it"),
        ] = None,
    ) -> RunSummary:
        """Apply a brand guide to one HTML artifact (web page or email), automatically.

        Writes branded.html, report.md, report.json and guide_rules.json into a new
        run folder. The original file is never modified. Rules that cannot be
        applied, cannot be interpreted, or contradict each other are reported with
        reasons, never guessed.
        """
        forced = ArtifactType(artifact_type) if artifact_type else None
        summary = orchestrator.run(guide_path, artifact_path, output_dir, forced)
        logger.info(
            "apply_brand finished run=%s status=%s changes=%d",
            summary.run_id,
            summary.status.value,
            summary.change_count,
        )
        return summary

    @mcp.tool(name="extract_rules", annotations=_READ_ONLY)
    @guarded("extract_rules")
    def extract_rules(
        guide_path: GuidePath,
        status: Annotated[
            str | None,
            Field(description="Only rules with this status, e.g. could_not_interpret"),
        ] = None,
        limit: Annotated[int, Field(ge=1, le=MAX_RULES_RETURNED)] = 500,
    ) -> ExtractedRules:
        """Show how a guide is read, without touching any artifact.

        Status 'pending' means the rule was understood; whether it applies depends
        on the artifact it is later used with.
        """
        wanted = _parse_status(status)
        name, interpretation = orchestrator.extract_rules(guide_path)
        rules = interpretation.rules
        counts = Counter(r.status.value for r in rules)
        selected = [r for r in rules if wanted is None or r.status is wanted]
        return ExtractedRules(
            guide=name,
            counts=dict(counts),
            total=len(rules),
            returned=min(len(selected), limit),
            truncated=len(selected) > limit,
            rules=[_view(r) for r in selected[:limit]],
            conflicts=interpretation.conflicts,
        )

    @mcp.tool(name="classify_artifact", annotations=_READ_ONLY)
    @guarded("classify_artifact")
    def classify_artifact(artifact_path: ArtifactPath) -> Classification:
        """Say whether an HTML file is a static web page or an email, and why."""
        return orchestrator.classify_file(artifact_path)

    @mcp.tool(name="get_report", annotations=_READ_ONLY)
    @guarded("get_report")
    def get_report(
        run_id: Annotated[
            str, Field(description="A run id such as run-20260102-030405-abc123")
        ],
        format: Annotated[
            Literal["markdown", "json"], Field(description="Report format")
        ] = "markdown",  # noqa: A002
    ) -> ReportText:
        """Return the saved report of an earlier run."""
        return ReportText(
            run_id=run_id,
            format=format,
            content=orchestrator.read_report(run_id, format),
        )

    @mcp.tool(name="list_plugins", annotations=_READ_ONLY)
    @guarded("list_plugins")
    def list_plugins() -> PluginList:
        """List the loaded plugins: readers, finders, handlers, appliers, and more."""
        return PluginList(plugins=registry.describe())

    @mcp.resource("report://{run_id}", mime_type="text/markdown")
    @guarded("report_resource")
    def report_resource(run_id: str) -> str:
        """The Markdown report of a run, readable as a resource."""
        return orchestrator.read_report(run_id, "markdown")


def _parse_status(status: str | None) -> RuleStatus | None:
    if status is None:
        return None
    try:
        return RuleStatus(status)
    except ValueError:
        allowed = ", ".join(s.value for s in RuleStatus)
        raise InvalidInputError(f"status must be one of: {allowed}") from None
