---
name: withdraw-earnings
description: Use when a tool author wants to check earnings or withdraw USDC to the settlement wallet.
applyTo: "**/*"
license: MIT
---

## Purpose

Guide tool authors through the payout lifecycle: inspect marketplace earnings
balance and per-call history, withdraw USDC to the registered settlement wallet,
and review past withdrawals. Use this after tools are live and earning — not
during initial publish (see `publish-tool`).

## Prerequisites

- `teardrop` on PATH (verify: `teardrop --version`)
- Authenticated as the tool author org (see auth gate below)
- Settlement wallet registered (typically via `teardrop tools publish --settlement-wallet 0x...`)
- Positive earnings balance for withdrawals

## Auth gate

```bash
teardrop auth status
```

Exit ≠ `0` → hand off to `install` skill.

## Workflow

### 1. Check earnings balance

```bash
teardrop earnings balance
```

This is marketplace author balance — distinct from org run credits
(`teardrop balance` in `manage-billing`).

### 3. Review per-call history

```bash
teardrop earnings history --limit 50
teardrop earnings history --limit 50 --tool get_weather
```

Use `--tool` to filter when diagnosing a specific listing.

### 4. Withdraw USDC

```bash
teardrop earnings withdraw 10.00
teardrop earnings withdraw 10.00 --yes          # skip confirmation
```

Funds settle on-chain to the registered settlement wallet, typically within
**1–5 minutes**.

Do not attempt withdrawals without a registered settlement wallet — complete
that via `publish-tool` / `teardrop tools publish --settlement-wallet 0x...`
first.

### 5. Audit past payouts

```bash
teardrop earnings withdrawals --limit 20 --json
```

### 6. Related balances (do not confuse them)

| Balance | Command | Meaning |
|---------|---------|---------|
| Author earnings | `teardrop earnings balance` | USDC earned from tool calls; withdrawable |
| Org credits | `teardrop balance` | Credits to *spend* on agent runs (not withdrawable here) |

## Reference

- CLI reference — Earnings & withdrawals: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#earnings--withdrawals
- CLI reference — Tool management (settlement wallet): https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#tool-management
- CLI reference — Exit codes: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#exit-codes
- README — Earn: https://github.com/teardrop-ai/teardrop-cli/blob/main/README.md

## Troubleshooting

| Symptom | Recovery |
|---------|----------|
| No settlement wallet | Publish/update path with `--settlement-wallet 0xChecksumAddress` |
| Withdraw rejected (zero/low balance) | `earnings balance` + `earnings history`; wait for settled tool calls |
| Withdrawal pending | Wait 1–5 minutes; check `earnings withdrawals` |
| Confused with org credits | Credits (`teardrop balance`) fund runs; earnings fund author payouts |
| Auth / permission errors | Re-auth as the author org; confirm tool ownership via `tools list` |
| Exit code `2` | Invalid amount or flags — fix input and retry |

## Missing inputs & fallbacks

| Missing | Agent action |
|---------|--------------|
| No withdrawal amount | Run `teardrop earnings balance` first. Suggest `min(balance, 10.00)` USDC as the amount. Ask the user to confirm. |
| No settlement wallet | Cannot withdraw. Run `teardrop tools list` to check existing tools; if none, hand off to `publish-tool` to publish with `--settlement-wallet`. If tools exist, use `teardrop tools update <tool> --settlement-wallet 0x...`. |
| No tool filter for history | Omit `--tool` — show all earnings history. |
| User confused about balance vs credits | Show the comparison table in step 6. Credits (`teardrop balance`) fund runs; earnings (`teardrop earnings balance`) are withdrawable USDC. |

