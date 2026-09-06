"""Core shortening logic."""

import random
import string
from datetime import datetime, timezone

from .store import LinkNotFoundError, LinkRecord, store

__all__ = [
    "LinkExpiredError",
    "LinkNotFoundError",
    "create_link",
    "generate_code",
    "list_links",
    "resolve",
    "stats",
    "to_utc",
]

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6


class LinkExpiredError(Exception):
    """Raised when a link exists but its expiry has passed - see main.py for
    the 410 translation.

    Lives here, not in store.py, on purpose: a domain exception belongs in the
    layer that actually detects the problem. A lookup miss is store.py's
    concern (LinkNotFoundError); expiry is a business rule layered on top of
    storage, not a storage concept, so it's shortener.py's concern. The next
    "this link can't be resolved" rule (e.g. a disabled/blocklisted link)
    should follow the same test: does raising it require knowing the record
    exists at all (store.py), or does it require a business rule about an
    otherwise-valid record (shortener.py)?"""


def generate_code() -> str:
    return "".join(random.choice(ALPHABET) for _ in range(CODE_LENGTH))


def to_utc(value: datetime) -> datetime:
    """Normalize a naive datetime to UTC; leave an aware one unchanged. Shared
    by models.py's validator and create_link() below - this module is meant
    to be callable directly (the test suite does exactly that), so it can't
    rely on the HTTP boundary having already normalized its input. Without
    this, resolve() crashes with TypeError comparing a naive expires_at
    against an aware datetime.now(timezone.utc), instead of failing 500->never
    or behaving correctly - confirmed by direct reproduction, not theoretical."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def create_link(url: str, expires_at: datetime | None = None) -> LinkRecord:
    # check-then-act, not atomic: fine for this in-memory, single-process workshop
    # store under test/demo traffic, but not a concurrency guarantee - two
    # requests could still race between exists() and put() under real load.
    if expires_at is not None:
        expires_at = to_utc(expires_at)
    code = generate_code()
    while store.exists(code):
        code = generate_code()
    record = LinkRecord(code=code, url=url, expires_at=expires_at)
    store.put(record)
    return record


def resolve(code: str) -> LinkRecord:
    record = store.get(code)
    if record.expires_at is not None and record.expires_at <= datetime.now(timezone.utc):
        # Not a follow (docs/link-expiry-acceptance-criteria.md Rule 4) - raise
        # before incrementing clicks, not after.
        raise LinkExpiredError(code)
    record.clicks += 1
    return record


def stats(code: str) -> LinkRecord:
    return store.get(code)


def list_links() -> list:
    return store.all()
