"""Format-neutral representation of a design guide."""

from collections.abc import Iterator
from enum import StrEnum

from pydantic import BaseModel, Field

from brand_compliance.models.source import SourceSpan


class NodeKind(StrEnum):
    """Kinds of node a guide tree can contain."""

    SECTION = "section"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    CODE = "code"
    TOKEN_SET = "token_set"  # noqa: S105 (a node kind, not a secret)


class GuideNode(BaseModel):
    """One node of the guide tree; every node keeps its source location."""

    kind: NodeKind
    span: SourceSpan
    text: str = ""
    level: int | None = None
    language: str | None = None
    header: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    row_lines: list[int] = Field(default_factory=list)
    tokens: dict[str, str] = Field(default_factory=dict)
    children: list["GuideNode"] = Field(default_factory=list)

    def walk(self) -> Iterator["GuideNode"]:
        """Yield this node and all descendants, depth first."""
        yield self
        for child in self.children:
            yield from child.walk()


class GuideDocument(BaseModel):
    """A whole guide, whatever format it was read from."""

    source_name: str
    source_format: str
    nodes: list[GuideNode] = Field(default_factory=list)

    def walk(self) -> Iterator[GuideNode]:
        """Yield every node in the document, depth first."""
        for node in self.nodes:
            yield from node.walk()

    def nodes_of(self, kind: NodeKind) -> list[GuideNode]:
        """Return every node of the given kind."""
        return [node for node in self.walk() if node.kind is kind]
