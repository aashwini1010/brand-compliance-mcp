"""Run the evaluation: ``python -m brand_compliance.evaluation``."""

import argparse
import logging
import sys
import tempfile
from pathlib import Path

from brand_compliance.core.errors import BrandComplianceError
from brand_compliance.core.logging import configure_logging
from brand_compliance.evaluation.cases import load_cases
from brand_compliance.evaluation.runner import EvalRunner
from brand_compliance.evaluation.scorecard import to_json, to_markdown

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    """Run every case, write the scorecard, and return 0 only if all passed."""
    parser = argparse.ArgumentParser(description="Evaluate the brand compliance tool")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root")
    parser.add_argument("--cases", type=Path, help="folder of case files")
    parser.add_argument(
        "--reports", type=Path, help="where to keep reports and the scorecard"
    )
    args = parser.parse_args(argv)
    configure_logging(logging.WARNING)
    root = args.root.resolve()
    cases_dir = args.cases or root / "eval" / "expected"
    reports = args.reports or root / "eval" / "reports"
    try:
        cases = load_cases(cases_dir)
        with tempfile.TemporaryDirectory(prefix="brand-eval-") as work:
            results = EvalRunner(root, Path(work)).run_all(cases, reports)
    except BrandComplianceError as exc:
        logger.error("Evaluation could not run: [%s] %s", exc.code, exc)
        return 2
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "scorecard.md").write_text(to_markdown(results), encoding="utf-8")
    (reports / "scorecard.json").write_text(to_json(results), encoding="utf-8")
    passed = sum(r.passed for r in results)
    print(f"{passed}/{len(results)} cases passed; scorecard in {reports}")  # noqa: T201
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
