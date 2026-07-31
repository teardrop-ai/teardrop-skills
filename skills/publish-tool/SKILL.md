---
name: publish-tool
description: Scaffold, probe, publish, and manage Teardrop marketplace tools end-to-end.
applyTo: "**/*"
---

## Purpose

Help a tool author go from idea to live marketplace tool: scaffold a spec, validate
the webhook, publish with pricing and settlement wallet, then list/update/pause/delete
as needed. Use this skill for authoring and lifecycle management of tools — not for
payouts (see `withdraw-earnings`).

## Prerequisites

- `teardrop` on PATH (comes with `teardrop-skills` — verify: `teardrop --version`)
- Authenticated session (see auth gate below)
- Reachable webhook endpoint for the tool
- Settlement wallet address before first payout-capable publish
- Tool name matching `^[a-z][a-z0-9_]*$`, ≤ 64 characters

## Auth gate

Before any mutating command, run:

```bash
teardrop auth status
```

If exit code ≠ `0` or no identity shown, hand off to the `install` skill first.

## Workflow

### 1. Scaffold a tool spec

```bash
teardrop tools init my_tool
# optional:
teardrop tools init my_tool --out custom.json --force
teardrop tools init premium --with-marketplace   # include MCP + price fields
```

Edit the generated JSON: set `webhook_url`, schemas, auth headers, and price.

**Pricing:** `base_price_usdc` is atomic USDC (6 decimals). Example: `5000` = **$0.005** per call.

### 2. Probe webhook health before publish

```bash
teardrop tools probe --from-file tool.json
```

For a published tool:

```bash
teardrop tools probe <tool-name>
teardrop tools probe <tool-name> --method GET --payload '{"test":"data"}'
teardrop tools probe <tool-name> \
  --auth-header-name X-Webhook-Secret \
  --auth-header-value s3cr3t
```

Probe exit codes:

- `0` — success (2xx–3xx); 4xx responses warn but still exit `0`
- `1` — timeout, 5xx, or connection error

Do not publish until probe is healthy for the intended auth/method.

### 3. Publish

Interactive wizard:

```bash
teardrop tools publish
```

From file (recommended for agents):

```bash
teardrop tools publish --from-file tool.json \
  --settlement-wallet 0xYourChecksumAddress
```

**Settlement wallet guidance:**
- If the user authenticated via SIWE (`--siwe --generate-wallet`), the generated
  Ethereum address can be used as the settlement wallet. Confirm with the user
  before passing it.
- If the user authenticated via email, they must provide a checksummed `0x`
  Ethereum address. Do not invent one — ask explicitly.
- Settlement wallet registration is required once before the first payout.
  It can be set on publish or later via `teardrop tools update <tool> --settlement-wallet 0x...`.

### 4. End-to-end first-time publish chain

For a user publishing their first tool, follow this order:

1. **`install` skill** → install CLI, authenticate (SIWE preferred for wallet generation)
2. **This skill** → scaffold, probe, publish with settlement wallet
3. **`run-agent` skill** → test the tool with a quick agent run
4. **`manage-billing` skill** → check credits if runs fail
5. **`withdraw-earnings` skill** → only after earnings accumulate (not immediately)

### 5. Manage existing tools

```bash
teardrop tools list
teardrop tools info <tool-name>
teardrop tools update <tool-name> --price 0.003
teardrop tools update <tool-name> --description "Updated" --publish
teardrop tools pause <tool-name>
teardrop tools update <tool-name> --active          # re-enable
teardrop tools delete <tool-name>
teardrop tools delete <tool-name> --yes             # skip confirmation
```

After changing a webhook URL, re-run `teardrop tools probe <tool-name>`.

### 6. Optional: inspect agent-visible tools

```bash
teardrop agent-tools list
```

Shows platform tools, marketplace subscriptions, and the org's own tools.

## Reference

- CLI reference — Tool management: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#tool-management
- CLI reference — Marketplace: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#marketplace
- CLI reference — Exit codes: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#exit-codes
- README — Publish a tool: https://github.com/teardrop-ai/teardrop-cli/blob/main/README.md

## Troubleshooting

| Symptom | Recovery |If SIWE auth: the generated Ethereum address is a candidate — confirm with user before using. If email auth: ask the user for a checksummed `0x` address. Do not invent one
|---------|----------|
| Invalid tool name | Use `^[a-z][a-z0-9_]*$`, max 64 chars |
| Probe exit `1` | Fix webhook uptime, TLS, timeout, or 5xx handler; retry probe |
| Probe 4xx (exit `0` with warning) | Fix auth headers / method; pass `--auth-header-*` overrides |
| Publish rejected | Ensure schemas are valid JSON Schema; webhook_url is HTTPS-reachable |
| Missing settlement wallet | Pass `--settlement-wallet 0x...` on publish (required once before payouts) |
| Need earnings / withdraw | Switch to the `withdraw-earnings` skill |
| Exit code `2` | Invalid flags or malformed file/JSON — fix input and retry |

## Missing inputs & fallbacks

| Missing | Agent action |
|---------|--------------|
| No webhook URL | Recommend the user deploy an endpoint first. For local dev: `ngrok http 8000` or `localtunnel`. If the user has no endpoint, scaffold with `--with-marketplace` (includes MCP fields) and explain they need a public HTTPS URL. |
| No tool name | Derive from the user's description: lowercase snake_case, `^[a-z][a-z0-9_]*$`, ≤ 64 chars. Example: "a weather checker" → `weather_checker`. |
| No price | Default to `5000` atomic USDC ($0.005 per call). Explain the user can change it later with `tools update`. |
| No settlement wallet | Run `teardrop auth login --siwe --generate-wallet --save-key` — the SIWE pubkey becomes the wallet address. Use that address for `--settlement-wallet`. If user prefers email auth, ask them to provide a checksummed Ethereum address. |
| No input/output schema | Scaffold with `tools init` which generates placeholder schemas. Ask the user to describe inputs/outputs, then edit the JSON. |
| Auth header unknown | Probe without auth first; if 4xx, ask the user for header name/value. |

## Exit codes

- `0` — success
- `1` — error (auth, API, probe failure)
- `2` — invalid input
