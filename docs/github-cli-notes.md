# Opening a PR in M2

You should already have `gh` authenticated under your own GitHub account, done as pre-work — if
`gh auth status` doesn't show you logged in, sort that out before starting M2, not mid-exercise:

```bash
gh auth login
```

Once authenticated, Claude Code can run `gh` like any other terminal command — `gh pr create`,
`gh pr view`, `gh issue view`, and so on — instead of you leaving the terminal for the GitHub web
UI. Ask it to do something GitHub-shaped and it'll reach for the right `gh` subcommand on its own;
you don't need to name one.

## The M2 flow

1. **Review first.** Ask the agent to review the diff (or the relevant files) before anything is
   proposed as final. This is the "AI code review" step — treat its findings as a starting point
   for discussion, not a verdict.
2. **Verify as a mob before anything ships.** This is the rotation ritual: driver writes the
   prompt → agent acts → the mob reads the diff aloud together → the navigator challenges one
   thing → accept or reject. Do this *before* opening a PR, not after — the PR should already
   represent something the mob agreed with.
3. **Open the PR via `gh`**, once the mob has actually accepted the change. Ask for it directly,
   e.g.:
   > "Open a PR from this branch into our working branch titled '...', summarizing what the
   > review found and what we fixed."

   **Check the base repo before confirming.** If you're working in your own fork, `gh pr create`
   defaults to targeting the *upstream* repo — the one you forked from, not yours — exactly like
   GitHub's own web UI does. Left unchecked, you'd propose a PR against the facilitator's real
   repo instead of merging into your own working branch. Have the agent pass `--repo
   <your-fork-owner>/<repo>` explicitly (or confirm the base yourself) before it actually opens
   the PR.
4. **Read what comes back.** The agent will report a PR URL/number — open it and confirm the diff
   on GitHub matches what the mob just verified locally. A PR opened by an agent is still an agent
   claim until a human has looked at the rendered diff.

## What to expect the review to catch here

Two of the planted issues in this starter app are the kind an AI review typically surfaces fast:
missing input validation on link creation, and an unhandled lookup that turns a "not found" into a
server error. A third (short-code collisions) is subtler and easy for a quick pass to miss —
worth a deliberate "did we check for X?" prompt from the navigator rather than assuming the review
was exhaustive. Coverage of *review* is also a map of gaps, not a guarantee.

## Copilot equivalent

GitHub MCP (and Playwright MCP) ship enabled by default in Copilot's agent mode — if you're
driving with Copilot, that's the natural path instead of `gh`. The workflow above — review, mob
verification, then open the PR — is identical regardless of which agent or which mechanism opens
the PR; only the tool differs.

## Optional: GitHub MCP instead of `gh`

GitHub MCP is the same "external actions" agent-feature category as `gh`, structured as native
tool calls instead of shell commands. It's worth knowing about, but it's not what this workshop
depends on, for a concrete reason: **GitHub's official remote MCP server currently can't complete
OAuth** — it doesn't support Dynamic Client Registration, a live bug tracked upstream (search
"does not support dynamic client registration" against `anthropics/claude-code` or
`github/github-mcp-server` for the open issues). This was confirmed directly, not assumed: `claude
mcp add --transport http github https://api.githubcopilot.com/mcp/` adds the server, but both
`claude mcp login github` and the interactive `/mcp` → Authenticate flow fail with that exact
error. It isn't your setup — it's the server.

The workaround, if you want to try it anyway, is a Personal Access Token instead of OAuth:

1. Remove any broken OAuth-based entry first: `claude mcp remove github`
2. Generate a GitHub fine-grained PAT (Settings → Developer settings → Personal access tokens →
   Fine-grained tokens → Generate new token), scoped to just this repo, with **Pull requests**,
   **Issues**, and **Contents** set to read and write, and an expiration past the workshop date.
3. Add the server with the token as a header instead of OAuth — no browser step this time:
   ```bash
   claude mcp add --transport http github https://api.githubcopilot.com/mcp/ \
     --header "Authorization: Bearer YOUR_TOKEN_HERE"
   ```
   `claude mcp list` should now show `github` as connected immediately.

Treat the token like a password — it's per-attendee, never committed, and worth an explicit
expiration date so a forgotten token doesn't linger with standing repo access.
