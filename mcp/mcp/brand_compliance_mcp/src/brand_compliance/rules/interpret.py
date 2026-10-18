"""Interpret a whole guide: extractors, leftovers, normalizer, then conflicts."""

import logging
from dataclasses import dataclass

from brand_compliance.core.contracts import RuleExtractor
from brand_compliance.models.conflict import Conflict
from brand_compliance.models.guide import GuideDocument
from brand_compliance.models.rule import Rule, RuleCandidate
from brand_compliance.rules.conflicts import detect_conflicts
from brand_compliance.rules.leftovers import collect_unmatched
from brand_compliance.rules.normalize import normalize
from brand_compliance.rules.vocabulary import Vocabulary

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GuideInterpretation:
    """Everything learned from a guide: its rules and its contradictions."""

    rules: list[Rule]
    conflicts: list[Conflict]


def interpret_guide(
    document: GuideDocument,
    extractors: list[RuleExtractor],
    vocabulary: Vocabulary,
) -> GuideInterpretation:
    """Return every rule found in the guide, each with a status and reason."""
    candidates: list[RuleCandidate] = []
    for extractor in extractors:
        found = extractor.extract(document)
        logger.debug("Extractor %s found %d candidates", extractor.name, len(found))
        candidates.extend(found)
    candidates.extend(collect_unmatched(document, candidates))
    rules, conflicts = detect_conflicts(normalize(candidates, vocabulary), vocabulary)
    logger.info(
        "Interpreted guide %s: %d rules, %d conflicts",
        document.source_name,
        len(rules),
        len(conflicts),
    )
    return GuideInterpretation(rules=rules, conflicts=conflicts)
