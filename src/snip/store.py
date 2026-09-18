"""In-memory storage. Not persistent — fine for a workshop starter."""

from dataclasses import dataclass, field


class LinkNotFoundError(Exception):
    """Raised when a code has no matching link. Callers at the HTTP boundary
    translate this into a 404 — see main.py's exception handler."""


@dataclass
class LinkRecord:
    code: str
    url: str
    clicks: int = 0


@dataclass
class Store:
    _links: dict = field(default_factory=dict)

    def put(self, record: LinkRecord) -> None:
        self._links[record.code] = record

    def get(self, code: str) -> LinkRecord:
        try:
            return self._links[code]
        except KeyError:
            raise LinkNotFoundError(code) from None

    def exists(self, code: str) -> bool:
        return code in self._links

    def all(self) -> list:
        return list(self._links.values())


store = Store()
