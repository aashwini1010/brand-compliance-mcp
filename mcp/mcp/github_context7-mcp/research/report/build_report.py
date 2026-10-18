"""Build the interactive MCP report from the research data files.

Usage (from anywhere):  python3 research/report/build_report.py

Reads   research/data/tools-catalog.json, research/data/tool-schemas-raw.json
        and the tool tables in research/github-mcp.md and context7-mcp.md.
Writes, for each version:
  detailed  template.html        -> mcp-servers-report.html         + research/report/artifact.html
  simple    template-simple.html -> mcp-servers-report-simple.html  + research/report/artifact-simple.html
The mcp-*.html files are full pages to open in a browser; artifact*.html are the same pages
without <html>/<head>, for publishing.
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
ROOT = RESEARCH.parent

TESTED_NOTES = {
    "create_repository": "Created private repo aashwini1010/my-repo. Answer: its id and web address.",
    "create_or_update_file": "Added hello.py to the main branch. Answer: file details and the new commit.",
    "get_file_contents": "Read hello.py back. Answer: a note plus the file text print('Hello from GitHub MCP!').",
    "search_users": "Searched 'aashwini1010'. Answer: 1 matching user.",
    "search_code": "Searched 'hello.py'. Answer: 163,328 matching files across all of GitHub.",
    "get_me": "Benchmark, 3 runs: about 0.85 s each, about 500-byte answer.",
    "search_repositories": "Benchmark, 3 runs: about 1.2 s each for 5 results, about 2.7 KB.",
    "resolve-library-id": "'next.js' + a JWT-middleware question gave 5 matches; best /vercel/next.js. About 2.3 s.",
    "query-docs": "/vercel/next.js + 'middleware JWT cookie' gave doc snippets. About 2.6 s, about 7.1 KB.",
}
ROW = re.compile(r"\|\s*`([a-z_\-]+)`(?:\s*⚠️)?\s*\|\s*([^|]+?)\s*\|")


def plain_descriptions() -> dict:
    """First plain-English description of each tool from the markdown tables."""
    plain = {}
    for name in ("github-mcp.md", "context7-mcp.md"):
        for line in (RESEARCH / name).read_text(encoding="utf-8").splitlines():
            m = ROW.match(line)
            if m and m.group(1) not in plain:
                plain[m.group(1)] = m.group(2)
    return plain


def tool_rows() -> list:
    """Compact per-tool records for the page."""
    catalog = json.loads((RESEARCH / "data/tools-catalog.json").read_text())["tools"]
    raw = json.loads((RESEARCH / "data/tool-schemas-raw.json").read_text())["servers"]
    by_name = {(s, t["name"]): t for s, ts in raw.items() for t in ts}
    rows = []
    for r in catalog:
        t = by_name[(r["server"], r["tool"])]
        desc = re.split(r"\n\s*\n", (t.get("description") or "").strip())[0].replace("\n", " ")
        if len(desc) > 420:
            desc = desc[:417].rsplit(" ", 1)[0] + "…"
        rows.append({
            "n": r["tool"], "s": "gh" if r["server"] == "GitHub" else "c7",
            "a": r["area"], "g": r["group"], "ro": r["server_read_only"],
            "x": r["server_destructive"], "req": r["required"], "opt": r["optional"],
            "m": r["methods"], "t": TESTED_NOTES.get(r["tool"]), "tt": r["title"], "d": desc,
            "sb": len(json.dumps(t.get("input_schema") or {}, separators=(",", ":"))),
        })
    return rows


VERSIONS = (
    ("template.html", "mcp-servers-report.html", "artifact.html"),
    ("template-simple.html", "mcp-servers-report-simple.html", "artifact-simple.html"),
)


def build(template: str, page_out: str, artifact_out: str, rows: list, plain: dict) -> None:
    """Fill one template with the data and write its two output files."""
    safe = lambda obj: json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (HERE / template).read_text(encoding="utf-8")
    page = page.replace("__TOOLS__", safe(rows)).replace("__PLAIN__", safe(plain))
    (HERE / artifact_out).write_text(page, encoding="utf-8")
    head, body = page.split("</style>", 1)
    full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f"{head}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n")
    (ROOT / page_out).write_text(full, encoding="utf-8")
    print(f"{template} -> {ROOT / page_out} and {HERE / artifact_out}")


def main() -> None:
    rows, plain = tool_rows(), plain_descriptions()
    missing = [r["n"] for r in rows if r["n"] not in plain]
    if missing:
        raise SystemExit(f"No plain description in the markdown for: {missing}")
    for template, page_out, artifact_out in VERSIONS:
        build(template, page_out, artifact_out, rows, plain)


if __name__ == "__main__":
    main()
