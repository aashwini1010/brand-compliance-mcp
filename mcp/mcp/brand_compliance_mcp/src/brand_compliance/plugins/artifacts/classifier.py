"""Decide whether HTML is a static web page or an email, and say why.

Email and web pages render very differently, so a wrong guess is costly. The
classifier collects weighted signals for both sides. When the evidence is
close it reports ``ambiguous`` and picks the email strategy (inline, safe
everywhere) and never silently guesses.
"""

import re
from typing import Final

from lxml.html import HtmlElement

from brand_compliance.models.artifact import ArtifactType, Classification
from brand_compliance.plugins.artifacts.base import parse_artifact_html

_AMBIGUOUS_BAND: Final = (0.35, 0.65)
_MIN_EVIDENCE: Final = 3.0
_MSO_COMMENT: Final = re.compile(r"\[if[^\]]*mso", re.IGNORECASE)
_LAYOUT_TABLE_XPATH: Final = (
    "//table[@role='presentation' or @cellpadding='0' or @cellspacing='0' "
    "or @border='0']"
)
_LANDMARKS_XPATH: Final = "//main | //nav | //section | //article | //header | //footer"


def classify_html(root: HtmlElement, raw: str) -> Classification:
    """Return the verdict with the evidence behind it."""
    email: list[tuple[float, str]] = []
    static: list[tuple[float, str]] = []
    _email_signals(root, raw, email)
    _static_signals(root, raw, static)
    email_points = sum(points for points, _ in email)
    static_points = sum(points for points, _ in static)
    total = email_points + static_points
    signals = [f"email +{p:g}: {why}" for p, why in email] + [
        f"static +{p:g}: {why}" for p, why in static
    ]
    if email_points == 0:
        # Email markup is a positive signature (layout tables, Outlook comments,
        # inline-style-heavy markup). With none of it, this is an ordinary page.
        return Classification(
            artifact_type=ArtifactType.STATIC,
            confidence=0.9 if static_points else 0.7,
            ambiguous=False,
            signals=[*signals, "no email markup found"],
        )
    if total < _MIN_EVIDENCE:
        return Classification(
            artifact_type=ArtifactType.EMAIL,
            confidence=0.5,
            ambiguous=True,
            signals=[*signals, "too little evidence either way"],
        )
    email_share = email_points / total
    ambiguous = _AMBIGUOUS_BAND[0] <= email_share <= _AMBIGUOUS_BAND[1]
    is_email = email_share >= 0.5
    return Classification(
        artifact_type=ArtifactType.EMAIL if is_email else ArtifactType.STATIC,
        confidence=round(email_share if is_email else 1 - email_share, 2),
        ambiguous=ambiguous,
        signals=signals,
    )


def _email_signals(root: HtmlElement, raw: str, found: list[tuple[float, str]]) -> None:
    layout_tables = root.xpath(_LAYOUT_TABLE_XPATH)
    if layout_tables:
        found.append((3, f"{len(layout_tables)} layout table(s)"))
    if len(root.xpath("//table//table")) >= 1:
        found.append((1, "nested tables"))
    if _MSO_COMMENT.search(raw):
        found.append((3, "Outlook (MSO) conditional comments"))
    if "urn:schemas-microsoft-com" in raw:
        found.append((2, "Microsoft Office XML namespaces"))
    if root.xpath("//meta[@name='x-apple-disable-message-reformatting']"):
        found.append((2, "email-client meta tag"))
    if re.search(r"mso-[a-z-]+\s*:", raw):
        found.append((2, "mso-* CSS properties"))
    if root.xpath("//*[@bgcolor or @valign]"):
        found.append((1, "legacy bgcolor/valign attributes"))
    if root.xpath("//center"):
        found.append((1, "<center> element"))
    elements = [e for e in root.iter() if isinstance(e.tag, str)]
    styled = sum(1 for e in elements if e.get("style"))
    if elements and styled / len(elements) > 0.5:
        found.append((2, f"{styled} of {len(elements)} elements carry inline styles"))
    if re.search(r"display:\s*none[^\"]*max-height:\s*0", raw):
        found.append((1, "hidden preheader text"))


def _static_signals(
    root: HtmlElement, raw: str, found: list[tuple[float, str]]
) -> None:
    scripts = [
        s for s in root.xpath("//script") if s.get("type") in (None, "", "module")
    ]
    if scripts:
        found.append((3, f"{len(scripts)} executable script(s) (emails strip scripts)"))
    if root.xpath("//link[@rel='stylesheet']"):
        found.append((1, "external stylesheet link"))
    landmarks = root.xpath(_LANDMARKS_XPATH)
    if landmarks:
        found.append((2, f"{len(landmarks)} semantic landmark element(s)"))
    css = "\n".join(style.text or "" for style in root.iter("style"))
    if re.search(r"display:\s*(flex|grid)", css):
        found.append((2, "flexbox/grid layout in CSS"))
    if re.search(r"--[\w-]+\s*:", css):
        found.append((1, "CSS custom properties"))
    if not root.xpath(_LAYOUT_TABLE_XPATH) and not _MSO_COMMENT.search(raw):
        found.append((1, "no layout tables and no Outlook markup"))


def classify_text(text: str) -> Classification:
    """Parse HTML text and classify it (convenience for callers without a tree)."""
    return classify_html(parse_artifact_html(text).root, text)
