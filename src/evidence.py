"""Evidence primitives for AlphaOS signals and decisions."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Evidence:
    """A small, structured proof item used by AlphaOS reasoning."""

    source: str
    label: str
    value: Any
    note: str | None = None
    weight: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the evidence into a JSON-friendly dictionary."""
        return {key: value for key, value in asdict(self).items() if value is not None}
