---
name: withdraw-earnings
description: Check marketplace earnings and withdraw USDC to the registered settlement wallet.
applyTo: "**/*"
---

## Purpose

Guide tool authors through the payout lifecycle: inspect marketplace earnings
balance and per-call history, withdraw USDC to the registered settlement wallet,
and review past withdrawals. Use this after tools are live and earning — not
during initial publish (see `publish-tool`).

## Prerequisites

- Teardrop CLI (`pip install teardrop-cli`, Python ≥ 3.11)
- Authenticated session as the tool author org (`teardrop auth status`)
- Settlement wallet already registered (typically during first
  `teardrop tools publish --settlement-wallet 0x...`)
- Positive earnings balance for withdrawals

## Workflow

### 1. Confirm auth

```bash
teardrop auth status
```

### 2. Check earnings balance

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

## Exit codes

- `0` — success
- `1` — error (auth, rate limit, API, withdraw failure)
- `2` — invalid input
