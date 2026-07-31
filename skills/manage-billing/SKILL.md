---
name: manage-billing
description: Check Teardrop credit balance and usage; direct users to the dashboard for top-ups.
applyTo: "**/*"
---

## Purpose

Inspect organization credits, spending limits, and historical usage so the user
understands burn rate and why an agent run may have paused. The CLI cannot add
funds — top-ups and payment methods are dashboard-only.

## Prerequisites

- `teardrop` on PATH (comes with `teardrop-skills` — verify: `teardrop --version`)
- Authenticated session (see auth gate below)

## Auth gate

```bash
teardrop auth status
```

If exit code ≠ `0` → hand off to `install` skill.

## Workflow

### 1. Check credit balance

```bash
teardrop balance
teardrop balance --json
```

Reports credit balance, spending limit, and daily spend.

Optional history (when available in the installed CLI):

```bash
teardrop balance credit-history
```

### 3. Inspect usage

```bash
teardrop usage
teardrop usage --start 2026-01-01 --end 2026-01-31
teardrop usage --json
```

Use date filters to explain spend over a window (token + run totals).

### 4. Top up (dashboard only)

The CLI does **not** support direct top-ups. Direct the user to:

**https://teardrop.dev/billing**

If a run fails for insufficient credit, the agent/runtime also surfaces this link.
Do not invent CLI top-up commands.

### 5. Explain the credit model (when the user asks)

- **Non-BYOK orgs:** Teardrop shared provider keys — credits or x402 cover model
  token costs **plus** the platform fee.
- **BYOK orgs:** Provider billed via the org's encrypted key; credits or x402 still
  cover the Teardrop orchestration fee. BYOK uses the configured model; pooled
  smart routing is disabled.
- **Promotional credit:** May be granted after email verification when the
  server-side program is enabled. Not available to SIWE users or marketplace
  author tools. A real top-up removes promotional restrictions. Do not assume
  eligibility or a fixed amount.

For LLM key / routing changes, use the `manage-org` skill (`llm-config`).

## Reference

- CLI reference — Billing & credits: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#billing--credits
- CLI reference — Exit codes: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#exit-codes
- Dashboard billing: https://teardrop.dev/billing

## Troubleshooting

| Symptom | Recovery |
|---------|----------|
| Agent paused / insufficient credit | `teardrop balance` then open https://teardrop.dev/billing |
| Unexpected spend | `teardrop usage --start YYYY-MM-DD --end YYYY-MM-DD --json` |
| Auth errors on balance/usage | Re-authenticate via `install` skill |
| User asks to top up in CLI | Explain dashboard-only path; do not fabricate commands |
| BYOK still needs credits | Expected — orchestration fee still requires credits or x402 |
| Exit code `2` | Invalid date/flags — correct input and retry |

## Missing inputs & fallbacks

| Missing | Agent action |
|---------|--------------|
| No date range for usage | Omit `--start`/`--end` — shows all-time totals. If the user asks about a specific period, ask for dates. |
| User wants to top up | Direct to https://teardrop.dev/. The CLI has no top-up command. Do not fabricate one. |
| User asks "why did my run fail?" | Run `teardrop balance` and `teardrop usage`. If balance is low/zero, explain credits are exhausted and link to dashboard. |
| User confused about BYOK + credits | Explain: BYOK pays the model provider directly but Teardrop still charges an orchestration fee (credits or x402). See `manage-org` for BYOK setup. |

## Exit codes

- `0` — success
- `1` — error (auth, rate limit, API)
- `2` — invalid input
