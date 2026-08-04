---
name: run-agent
description: Use when the user wants to run an agent, continue a chat, or automate with schedules/event triggers.
applyTo: "**/*"
license: MIT
---

## Purpose

Execute Teardrop agents for the user: one-shot `run`, stateful `chat`, recurring
`schedules`, and webhook-driven `event-triggers`. Use this skill whenever the user
wants to prompt an agent, continue a thread, estimate cost, or automate runs.

## Prerequisites

- `teardrop` on PATH (verify: `teardrop --version`)
- Auth + sufficient credits/x402 for paid runs (see `manage-billing` if runs fail on credit)
- Optional: tool policy file, context JSON, marketplace subscriptions

## Auth gate

```bash
teardrop auth status
```

Exit ≠ `0` → hand off to `install` skill. Empty balance + failing runs → `manage-billing`.

## Workflow

### 1. One-shot agent run (`teardrop run`)

Best for scripts and single prompts:

```bash
teardrop run "What is the current ETH gas price?"
teardrop run "Follow up" --thread <thread-id>
teardrop run "Process this order" --context '{"order_id":"ord_123"}'
teardrop run "Summarize news" --exclude platform/web_search
teardrop run "Analyze this data" --estimate-cost
teardrop run "Execute workflow" --policy-file policy.json
teardrop run "..." --json --no-stream
teardrop run "..." --json --with-ui          # UI components; ~60s extra overhead
```

Default CLI output is automation-friendly (`emit_ui=false`). Use `--with-ui` only
when structured UI component data is required.

**Long or multi-line prompts:** `teardrop run` / `teardrop chat` take the prompt
as a positional argument. For long or multi-line prompts, avoid unwieldy inline
one-liners — write the prompt to a file and read it into the argument (e.g.
`teardrop run "$(Get-Content prompt.txt -Raw)"` on PowerShell, or
`teardrop run "$(cat prompt.txt)"` on POSIX). For recurring schedules, use the
native `--prompt-file` flag (see step 4).

### 3. Stateful chat (`teardrop chat`)

Continues the same thread across invocations (stored in `~/.teardrop/config.toml`):

```bash
teardrop chat "What is the current ETH gas price?"   # creates/stores thread
teardrop chat "Follow up on that"                    # continues stored thread
teardrop chat "Start fresh" --new
teardrop chat "Specific thread" --thread thr_abc123
teardrop chat "..." --json
```

**Flag precedence (highest first):** `--new` → `--thread <id>` → stored thread → server-minted.

Chat accepts the same options as `run`: `--context`, `--exclude`, `--policy-file`,
`--estimate-cost`, `--with-ui`, `--no-stream`, `--base-url`.

Note: `teardrop auth logout` clears the active chat thread id.

### 4. Recurring schedules

```bash
teardrop schedules create \
  --name hourly-briefing \
  --prompt "Summarize open incidents" \
  --interval-seconds 3600 \
  --json

# Long/multi-line prompt from a UTF-8 file (or '-' for stdin)
teardrop schedules create \
  --name hourly-briefing \
  --prompt-file prompt.txt \
  --interval-seconds 3600 \
  --json

teardrop schedules list --json
teardrop schedules get <schedule-id> --json
teardrop schedules update <schedule-id> --enabled false --json
teardrop schedules update <schedule-id> --clear-callback-url
teardrop schedules runs <schedule-id> --limit 50 --json
teardrop schedules delete <schedule-id>
teardrop schedules delete <schedule-id> --yes
```

`--prompt` and `--prompt-file` are mutually exclusive — pass exactly one. Invalid
UTF-8 or unreadable files produce a clean CLI error. After creating or updating a
schedule, verify with `teardrop schedules get <schedule-id> --json`.

Schedules are **interval-only** (`--interval-seconds`); there is no cron syntax or
timezone field. For "daily at 9am", compute the interval from now.

### 5. Event triggers (signed inbound webhooks)

```bash
teardrop event-triggers create \
  --name inbound-orders \
  --prompt "Validate and process this order payload" \
  --json

teardrop event-triggers list --json
teardrop event-triggers get <trigger-id> --json
teardrop event-triggers update <trigger-id> --enabled false --json
teardrop event-triggers update <trigger-id> --callback-url https://example.com/hook
teardrop event-triggers runs <trigger-id> --limit 50 --json
teardrop event-triggers rotate-secret <trigger-id> --json
teardrop event-triggers delete <trigger-id>
teardrop event-triggers delete <trigger-id> --yes
```

**Critical:** `create` and `rotate-secret` print the signing secret **once**. Store it
immediately. Later `list` / `get` / `update` never return the plaintext secret again.

### 6. Choose the right modality

| Need | Command |
|------|---------|
| One-shot / CI / scripts | `teardrop run` |
| Multi-turn conversation | `teardrop chat` |
| Time-based recurrence | `teardrop schedules ...` |
| Inbound webhook automation | `teardrop event-triggers ...` |

## Reference

- CLI reference — Running agents: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#running-agents
- CLI reference — Chat sessions: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#chat-sessions
- CLI reference — Schedules: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#schedules
- CLI reference — Event triggers: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#event-triggers
- JSON output schema: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-json-schema.md
- Exit codes: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#exit-codes

## Troubleshooting

| Symptom | Recovery |
|---------|----------|
| Run fails on credit | `teardrop balance`; open https://teardrop.dev/billing (CLI cannot top up) |
| Malformed `--context` | Exit `2` — pass valid JSON object string |
| Lost chat continuity | Check stored thread; use `--thread <id>` or `--new`; logout clears thread |
| Forgot trigger secret | `teardrop event-triggers rotate-secret <id>` and store the new secret immediately |
| Schedule/trigger failures | Inspect `... runs <id>` for status, cost, and error message |
| Need different tools | Subscribe via `discover-marketplace` or adjust `--exclude` / `--policy-file` |

## Missing inputs & fallbacks

| Missing | Agent action |
|---------|--------------|
| Empty or vague prompt | Ask **one** clarifying question: "What goal should the agent accomplish? Give me a concrete example of the output you want." Then formulate a specific prompt. |
| No thread ID for follow-up | Run `teardrop chat "<prompt>"` — it auto-continues the stored thread. If the user wants a fresh conversation, use `--new`. |
| No schedule interval | Ask the user how often (e.g., "every hour", "daily at 9am"). Convert to `--interval-seconds` (3600, 86400, etc.). |
| No event trigger name | Derive from the prompt: lowercase, hyphenated. Example: "process orders" → `inbound-orders`. |
| No policy file | Omit `--policy-file` — runs use default tool access. |
| No `--context` JSON | Omit `--context` — the agent works without structured context. |
| User wants cost estimate | Run with `--estimate-cost` (no run performed, just prints cost). |

