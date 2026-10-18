"""Where a piece of information came from."""

from pydantic import BaseModel, ConfigDict, Field


class SourceSpan(BaseModel):
    """Location of a fact inside a guide (file, lines or page, heading path)."""

    model_config = ConfigDict(frozen=True)

    file: str
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    page: int | None = Field(default=None, ge=1)
    heading_path: tuple[str, ...] = ()

    def describe(self) -> str:
        """Return a short human-readable location, e.g. ``guide.md:30``."""
        if self.line_start is not None:
            return f"{self.file}:{self.line_start}"
        if self.page is not None:
            return f"{self.file} p.{self.page}"
        return self.file
