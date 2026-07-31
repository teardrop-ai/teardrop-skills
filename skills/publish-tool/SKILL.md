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

- Teardrop CLI (`pip install teardrop-cli`, Python ≥ 3.11)
- Authenticated session (`teardrop auth status` → exit `0`)
- Reachable webhook endpoint for the tool
- Checksummed settlement wallet address before first payout-capable publish
- Tool name matching `^[a-z][a-z0-9_]*$`, ≤ 64 characters

## Workflow

### 1. Confirm auth

```bash
teardrop auth status
```

If unauthenticated, run the `install` skill first.

### 2. Scaffold a tool spec

```bash
teardrop tools init my_tool
# optional:
teardrop tools init my_tool --out custom.json --force
teardrop tools init premium --with-marketplace   # include MCP + price fields
```

Edit the generated JSON: set `webhook_url`, schemas, auth headers, and price.

**Pricing:** `base_price_usdc` is atomic USDC (6 decimals). Example: `5000` = **$0.005** per call.

### 3. Probe webhook health before publish

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

### 4. Publish

Interactive wizard:

```bash
teardrop tools publish
```

From file (recommended for agents):

```bash
teardrop tools publish --from-file tool.json \
  --settlement-wallet 0xYourChecksumAddress
```

Settlement wallet registration is required once before the first payout.

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

| Symptom | Recovery |
|---------|----------|
| Invalid tool name | Use `^[a-z][a-z0-9_]*$`, max 64 chars |
| Probe exit `1` | Fix webhook uptime, TLS, timeout, or 5xx handler; retry probe |
| Probe 4xx (exit `0` with warning) | Fix auth headers / method; pass `--auth-header-*` overrides |
| Publish rejected | Ensure schemas are valid JSON Schema; webhook_url is HTTPS-reachable |
| Missing settlement wallet | Pass `--settlement-wallet 0x...` on publish (required once before payouts) |
| Need earnings / withdraw | Switch to the `withdraw-earnings` skill |
| Exit code `2` | Invalid flags or malformed file/JSON — fix input and retry |

## Exit codes

- `0` — success
- `1` — error (auth, API, probe failure)
- `2` — invalid input
