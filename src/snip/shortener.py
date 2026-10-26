"""Core shortening logic."""

import random
import string

from .store import LinkRecord, store

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6


def generate_code() -> str:
    return "".join(random.choice(ALPHABET) for _ in range(CODE_LENGTH))


def create_link(url: str) -> LinkRecord:
    code = generate_code()
    while store.exists(code):
        code = generate_code()
    record = LinkRecord(code=code, url=url)
    store.put(record)
    return record


def resolve(code: str) -> LinkRecord:
    record = store.get(code)
    record.clicks += 1
    return record


def stats(code: str) -> LinkRecord:
    return store.get(code)


def list_links() -> list:
    return store.all()
