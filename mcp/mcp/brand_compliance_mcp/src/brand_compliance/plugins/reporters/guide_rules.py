"""The rules found in the guide, so a person can audit how it was read."""

import json
from pathlib import Path

from brand_compliance.models.report import SCHEMA_VERSION, RunResult


class GuideRulesReporter:
    """Writes ``guide_rules.json``: every rule (final status) and every conflict."""

    name = "guide-rules"
    format = "guide-rules"
    filename = "guide_rules.json"

    def render(self, result: RunResult, output_dir: Path) -> Path:
        """Write the rule list and return its path."""
        payload = {
            "schema_version": SCHEMA_VERSION,
            "guide": result.guide_name,
            "rules": [rule.model_dump(mode="json") for rule in result.rules],
            "conflicts": [c.model_dump(mode="json") for c in result.conflicts],
        }
        path = output_dir / self.filename
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return path
