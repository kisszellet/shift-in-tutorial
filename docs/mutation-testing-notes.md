# Mutation testing notes (M3a, updated M5b)

`docs/test-strategy.md` names `shortener.py` as mutmut's target — it carries the highest-risk
logic (validation, collision handling, lookup). Run it with:

```bash
pip install -e ".[test]"
mutmut run
mutmut results   # lists any survivors
mutmut show <id> # shows one survivor's diff
```

Config lives in `pyproject.toml`'s `[tool.mutmut]`. Two settings matter and are easy to get
wrong: `source_paths` controls what gets **copied** into mutmut's sandbox (`mutants/`), not just
what gets mutated — set it to `["src"]` so the whole package (and its imports) stays resolvable.
Use `only_mutate = ["src/snip/shortener.py"]` to actually scope *mutation generation* down to the
one file. Pointing `source_paths` at a single file (the more obvious-looking config) copies only
that file into the sandbox and breaks every test that imports anything else from `snip`.

## What the first run found

The first real run: **18 of 19 mutants killed, 1 survived.** The survivor, in
`create_link`'s collision-retry loop:

```diff
 def create_link(url: str) -> LinkRecord:
     code = generate_code()
     while store.exists(code):
-        code = generate_code()
+        code = None
     record = LinkRecord(code=code, url=url)
     store.put(record)
     return record
```

`test_create_link_retries_on_code_collision` forces exactly one collision (via `monkeypatch`) and
exercises this exact line — so the mutant *was* covered. The test still passed against it, because
the assertions only checked that the second link's code differed from the first and that both
still resolved. Under the mutant, `second.code` becomes `None`; `None != "dupe12"` is still true,
and `store.get(None)` still succeeds (the record is happily stored under key `None`). Both
assertions held on a code value that's actually broken — a `None` short code isn't a valid path
segment and would never come out of `generate_code()` for real.

This is the oracle problem, concretely: 100% line coverage on this file, and a test that exercises
the exact right branch, but an assertion too weak to notice the value it got back was garbage.

**Fix:** pin down what the retried value should actually be, not just that it differs:

```python
assert second.code == "uniq99"  # retried via generate_code(), not left blank
```

Re-ran mutmut: **19/19 killed.**

## Takeaway for the mob

A green coverage report answers "did this line run?" — not "would we notice if it broke?" Treat a
surviving mutant as a missing assertion until you've concretely shown otherwise (an equivalent
mutant that can't change observable behavior is possible in principle, but wasn't the case here).

## M5b: the same lesson showed up twice more in one feature

Building link expiry added real logic to `resolve()` — a comparison and an exception. First run:
**24 of 26 mutants killed, 2 survived.**

**Survivor 1 — boundary operator:** `record.expires_at <= datetime.now(...)` mutated to `<`. Every
test used a clearly-past timestamp (`now - 1 second`), so `<=` vs `<` made no difference to any of
them — the exact instant of expiry was never exercised. Fixed by freezing "now" (`monkeypatch` on
`shortener.datetime`) and constructing a record whose `expires_at` exactly equals it, then
asserting that still raises. Without this, a future refactor could silently make links valid
"through" their expiry instant instead of "up to and not including" it, and nothing would catch it.

**Survivor 2 — exception payload:** `raise LinkExpiredError(code)` mutated to
`raise LinkExpiredError(None)`. The test only checked *that* a `LinkExpiredError` was raised
(`pytest.raises(LinkExpiredError)`), never *which* code it carried — the same class of gap as the
`None`-short-code mutant above, just on an exception's payload instead of a return value. Fixed by
asserting `str(exc_info.value) == record.code`.

Second run: **26/26 killed.**

Same root cause both times: `pytest.raises(SomeError)` alone proves an error type, not that the
error is *correct*. If the exception (or the mutated code path) can carry meaningfully different
content, assert on the content too.
