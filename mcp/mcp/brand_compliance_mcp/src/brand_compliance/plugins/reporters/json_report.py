"""Machine-readable report."""

from pathlib import Path

from brand_compliance.models.report import Report, RunResult


class JsonReporter:
    """Writes the full run as ``report.json``."""

    name = "json"
    format = "json"
    filename = "report.json"

    def render(self, result: RunResult, output_dir: Path) -> Path:
        """Write the report and return its path."""
        path = output_dir / self.filename
        path.write_text(Report(run=result).model_dump_json(indent=2), encoding="utf-8")
        return path
