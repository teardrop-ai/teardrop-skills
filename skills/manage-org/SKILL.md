---
name: manage-org
description: Configure org LLM/BYOK settings, MCP servers, model benchmarks, and local CLI config.
applyTo: "**/*"
---

## Purpose

Manage organization-level Teardrop configuration: LLM provider/model/routing, BYOK
keys, attached MCP servers, model benchmarks, and the local `~/.teardrop/config.toml`
settings. Use this skill for platform setup — not for end-user agent prompts
(`run-agent`) or credit top-ups (`manage-billing`).

## Prerequisites

- Teardrop CLI (`pip install teardrop-cli`, Python ≥ 3.11)
- Authenticated session for org-mutating commands (`llm-config`, `mcp`)
- `models benchmarks` public catalogue works without auth; `--org` metrics need auth

## Workflow

### 1. Confirm auth (for mutating commands)

```bash
teardrop auth status
```

### 2. LLM configuration

Inspect current config (5-minute cache by default):

```bash
teardrop llm-config get
teardrop llm-config get --json --no-cache
```

One-shot BYOK wizard:

```bash
teardrop llm-config byok
```

Set provider, model, and routing:

```bash
# Quality tier (default)
teardrop llm-config set --provider anthropic --model claude-sonnet-4-6 --routing quality

# Cost tier
teardrop llm-config set --provider openrouter --model deepseek-chat --routing cost

# Speed tier
teardrop llm-config set --provider google --model gemini-3-flash --routing speed

# Advanced tuning
teardrop llm-config set \
  --provider anthropic \
  --model claude-sonnet-4-6 \
  --max-tokens 8000 \
  --temperature 0.7 \
  --timeout-seconds 60
```

**Providers:** `openrouter`, `google`, `anthropic`, `openai`  
**Routing:** `default` · `cost` · `speed` · `quality`  
**Validation:** temperature 0.0–2.0 · max tokens 1–200,000 · timeout ≥ 1s

BYOK key handling (never echo secrets into logs or commits):

```bash
# Stdin pipe preferred (stays out of shell history)
# Unix:  cat "$key_file" | teardrop llm-config set --provider anthropic --model claude-sonnet-4-6 --byok-key -
# PowerShell:
Get-Content "$key_file" | teardrop llm-config set `
  --provider anthropic --model claude-sonnet-4-6 --byok-key -

# Remove BYOK key
teardrop llm-config set --provider anthropic --model claude-sonnet-4-6 --clear-key
```

Revert to platform defaults:

```bash
teardrop llm-config delete
```

**Credit note:** BYOK pays the model provider directly but still needs Teardrop
credits or x402 for the orchestration fee. See `manage-billing`.

### 3. MCP servers

Attach external Model Context Protocol servers; their tools become available to agents:

```bash
teardrop mcp list
teardrop mcp add --name "my-server" --url https://mcp.example.com
teardrop mcp add --name "secure" --url https://mcp.example.com \
  --auth-type bearer --auth-token <token>
teardrop mcp discover <server-id>
teardrop mcp remove <server-id> --yes
```

### 4. Models & benchmarks

```bash
teardrop models benchmarks                      # public catalogue (no auth)
teardrop models benchmarks --json --no-cache
teardrop models benchmarks --org <org-id>       # org actuals (auth)
teardrop models benchmarks --org <org-id> --force-refresh
```

Public view: P95 latency, per-token pricing, 7-day volume per tier.  
Org view: average latency, cost per run, tokens per second.

### 5. Local CLI configuration file

Stored at `~/.teardrop/config.toml` (mode `0600` on POSIX). Secrets live in the
OS keyring, not this file.

```bash
teardrop config list                  # tokens redacted to first 12 chars
teardrop config get api_url
teardrop config set api_url https://api.teardrop.dev

teardrop init                         # explicit bootstrap
teardrop init --base-url https://api.teardrop.dev
```

Writable keys: `api_url`, `email`, `org_id`. Tokens/secrets only via `auth login` / `auth logout`.

## Reference

- CLI reference — LLM configuration: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#llm-configuration
- CLI reference — MCP servers: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#mcp-servers
- CLI reference — Models & benchmarks: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#models--benchmarks
- CLI reference — Configuration file: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#configuration-file
- Exit codes: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#exit-codes

## Troubleshooting

| Symptom | Recovery |
|---------|----------|
| Invalid temperature / tokens / timeout | Stay within documented validation ranges |
| BYOK key in shell history | Use `--byok-key -` with stdin; rotate the exposed key |
| MCP tools missing in runs | `mcp list` → `mcp discover <id>`; confirm server URL/auth |
| Config set rejected for token fields | Manage tokens only through `auth login` / `logout` |
| Still out of credits after BYOK | Expected orchestration fee — use `manage-billing` |
| Exit code `2` | Invalid flags or values — fix input and retry |

## Exit codes

- `0` — success
- `1` — error (auth, rate limit, API)
- `2` — invalid input
