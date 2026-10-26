#!/usr/bin/env python3
"""Stop hook: run the suite; if it fails, block the stop and hand Claude the output.

Output shape (hooks docs, "Stop decision control"):
    {"decision": "block", "reason": "<why Claude should continue>"}
Exit 0 with no JSON lets Claude stop.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

TIMEOUT_S = 120
MAX_REASON_CHARS = 6000
TESTS = ["tests/unit", "tests/api"]


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or hook_input.get("cwd") or ".")
    venv_python = root / ".venv" / "bin" / "python"
    python = str(venv_python) if venv_python.exists() else sys.executable

    try:
        result = subprocess.run(
            [python, "-m", "pytest", *TESTS, "-q"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        output, returncode = f"pytest did not finish within {TIMEOUT_S}s", 1
    else:
        output, returncode = result.stdout + result.stderr, result.returncode

    # 0 = all passed, 5 = no tests collected: neither is a failing test.
    if returncode in (0, 5):
        return

    # Already continuing because of this hook: don't loop on a failure that
    # did not resolve. Let Claude stop so it can say it could not fix it.
    if hook_input.get("stop_hook_active"):
        return

    if len(output) > MAX_REASON_CHARS:
        output = "...(truncated)...\n" + output[-MAX_REASON_CHARS:]
    block(
        "The test suite is failing (pytest tests/unit tests/api). Fix it, or say "
        "clearly that you could not.\n\n" + output
    )


if __name__ == "__main__":
    main()
