---
name: discover-marketplace
description: Use when the user needs to find, evaluate, subscribe to, or unsubscribe from Teardrop marketplace tools.
applyTo: "**/*"
license: MIT
---

## Purpose

Help users find marketplace tools and attach them to their org so agents can call
them. Browsing and search work without authentication; subscribe/unsubscribe require
a signed-in session.

## Prerequisites

- `teardrop` on PATH (verify: `teardrop --version`)
- Network access to the Teardrop API
- Auth required only for `subscribe` / `subscriptions` / `unsubscribe`

## Auth gate (mutating commands only)

```bash
teardrop auth status
```

Exit ≠ `0` → hand off to `install` skill.

## Workflow

### 1. Browse and search (no auth required)

```bash
teardrop marketplace list
teardrop marketplace list --category data --json
teardrop marketplace search "weather"
teardrop marketplace info acme/weather
```

Tool identifiers use `org/name` form (example: `acme/weather`).

### 1b. Evaluate tool quality with public reputation (no auth required)

```bash
teardrop marketplace reputation
teardrop marketplace reputation acme/weather
teardrop marketplace reputation acme/weather --json
```

Public reputation shows aggregate quality metrics for active marketplace tools
(`score`, `success`, `sample`, `confidence`, `freshness`, `latency_ms`,
`callers`). Use it to help the user evaluate a tool's quality before
subscribing. Passing an `ORG/TOOL` filters to that exact tool; if there is no
match it prints `No public reputation found for '<name>'.` and exits `1`.
Empty data prints `No public reputation data available.` (exit `0`).

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
| Need to evaluate tool quality | `marketplace reputation [org/name]` (no auth required) |
| Need to publish your own tool | Use `publish-tool` skill |
| Exit code `2` | Invalid tool id or flags — fix input and retry |

## Missing inputs & fallbacks

| Missing | Agent action |
|---------|--------------|
| No search query | Run `teardrop marketplace list` first. Show the user the first 5–10 results and ask what looks relevant. If a category is guessable ("data", "weather", "finance"), use `--category`. |
| No tool ID for subscribe | Search first: `teardrop marketplace search "<keyword>"` to find the `org/name` identifier. |
| No auth for subscribe | Run `teardrop auth status`. If unauthenticated, hand off to the `install` skill first. |
| User wants to evaluate quality | Run `teardrop marketplace reputation` (all tools) or `teardrop marketplace reputation org/name` (one tool). |
| User wants to publish | Hand off to the `publish-tool` skill. |

