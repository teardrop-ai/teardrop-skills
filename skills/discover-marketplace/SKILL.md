---
name: discover-marketplace
description: Browse, search, subscribe, and unsubscribe Teardrop marketplace tools.
applyTo: "**/*"
---

## Purpose

Help users find marketplace tools and attach them to their org so agents can call
them. Browsing and search work without authentication; subscribe/unsubscribe require
a signed-in session.

## Prerequisites

- `teardrop` on PATH (comes with `teardrop-skills` — verify: `teardrop --version`)
- Network access to the Teardrop API
- Authenticated session for `subscribe` / `subscriptions` / `unsubscribe`

## Auth gate (subscribe/unsubscribe only)

```bash
teardrop auth status
```

If exit code ≠ `0` → hand off to `install` skill before subscribing.

## Workflow

### 1. Browse and search (no auth required)

```bash
teardrop marketplace list
teardrop marketplace list --category data --json
teardrop marketplace search "weather"
teardrop marketplace info acme/weather
```

Tool identifiers use `org/name` form (example: `acme/weather`).

### 2. Ensure auth before mutating subscriptions

```bash
teardrop auth status
```

If unauthenticated, run the `install` skill, then return here.

### 3. Subscribe

```bash
teardrop marketplace subscribe acme/weather
teardrop marketplace subscribe acme/weather --yes    # skip confirmation
```

Subscribed tools become available to the org's agents immediately.

### 4. Review and remove subscriptions

```bash
teardrop marketplace subscriptions
teardrop marketplace unsubscribe acme/weather
```

### 5. Verify agent visibility (optional)

```bash
teardrop agent-tools list
```

Confirms platform tools, subscriptions, and first-party tools visible to runs.

### 6. Run an agent that can use the tool

Hand off to the `run-agent` skill, for example:

```bash
teardrop run "Use marketplace weather data for London"
```

## Reference

- CLI reference — Marketplace: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#marketplace
- CLI reference — Exit codes: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#exit-codes
- README — Browse the marketplace: https://github.com/teardrop-ai/teardrop-cli/blob/main/README.md

## Troubleshooting

| Symptom | Recovery |
|---------|----------|
| Subscribe fails with auth error | `teardrop auth login` / `auth status`, then retry |
| Unknown tool id | `marketplace search` / `list`, then `info org/name` |
| Tool not used in a run | Confirm subscription; check `--exclude` / `--policy-file` on `run`/`chat` |
| Need to publish your own tool | Use `publish-tool` skill |
| Exit code `2` | Invalid tool id or flags — fix input and retry |

## Missing inputs & fallbacks

| Missing | Agent action |
|---------|--------------|
| No search query | Run `teardrop marketplace list` first. Show the user the first 5–10 results and ask what looks relevant. If a category is guessable ("data", "weather", "finance"), use `--category`. |
| No tool ID for subscribe | Search first: `teardrop marketplace search "<keyword>"` to find the `org/name` identifier. |
| No auth for subscribe | Run `teardrop auth status`. If unauthenticated, hand off to the `install` skill first. |
| User wants to publish | Hand off to the `publish-tool` skill. |

## Exit codes

- `0` — success
- `1` — error (auth, rate limit, API)
- `2` — invalid input
