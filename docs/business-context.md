# snip — business context

## What it is

**snip** is an internal URL-shortening service. Teams across the company paste long, ugly links
into chat, docs, and slides; snip turns them into short, shareable codes and counts how often each
short link is followed.

## Who uses it

- **Employees** creating short links for internal docs and dashboards.
- **Recipients** following short links (the highest-volume path by far).
- **Link owners** checking how many times their link was followed.

## Core capabilities (current)

1. Create a short link from a long URL, optionally with an expiry (M5b).
2. Follow a short link (redirect to the original URL, or `410 Gone` if expired).
3. List existing links.
4. See click stats for a link.

## Definition of Ready (DoR) — excerpt

- The user story has a clear actor, action, and outcome.
- Acceptance criteria are testable and agreed by the Three Amigos.
- Impact on the published SLIs is understood.

## Definition of Done (DoD) — excerpt

- Code reviewed and merged via PR.
- Tests exist at the appropriate level(s) and pass in CI.
- SLI-affecting changes are reflected in the pipeline gates.
- Observable behaviour changes are covered by at least one higher-level test.

## Link expiry (built in M5)

Owners can set an expiry on a short link; it stops resolving after that time. Went through
Example Mapping (M5a, `docs/link-expiry-acceptance-criteria.md`) before being built (M5b) — see
that doc for the confirmed rules and scenarios.
