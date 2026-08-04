---
name: install
description: Use when the user needs CLI install, authentication, login/signup, session checks, or first-time onboarding.
applyTo: "**/*"
license: MIT
---

## Purpose

Get a user from zero to a working Teardrop session: install the CLI, create or
sign into an account/org, verify identity, and optionally run the guided
quickstart. Use this skill whenever the user needs onboarding, login, signup,
session checks, or logout.

## Prerequisites

- Python ≥ 3.11; `teardrop` on PATH (verify: `teardrop --version`)
- Network access to PyPI and the Teardrop API
- SIWE: ability to generate/supply an Ethereum private key (never commit keys)
- Email auth: password ≥ 8 chars with ≥ 1 digit

## Glossary (shared terms)

- **Marketplace tool** — a published tool others subscribe to; **agent tool** — a tool an agent can call.
- **Credits** — org balance spent on runs (`teardrop balance`); **earnings** — author USDC payouts (`teardrop earnings balance`).
- **run** — one-shot execution; **chat** — stateful multi-turn thread.

## Workflow

### 1. Verify CLI is installed

```bash
teardrop --version
```

Exit code `0` confirms the binary is on `PATH`. If not found, reinstall:
`pip install teardrop-skills`.

**Locate the binary if it's not on PATH.** When installed into a virtualenv,
the `teardrop` executable may land in a `Scripts/` (Windows) or `bin/`
(POSIX) directory that isn't on `PATH`. Check for it before assuming the
install failed:

```powershell
# Windows (venv)
Get-ChildItem venv/Scripts/teardrop*

# POSIX (venv)
ls venv/bin/teardrop
```

If present, invoke it directly (e.g. `venv/Scripts/teardrop --version`) or add
that directory to `PATH`.

### 2. Prefer guided onboarding when the user is new

```bash
teardrop quickstart
```

Quickstart covers sign-in, optional BYOK LLM setup, and a first agent run or
tool scaffold. Local tool scaffolding and public marketplace browsing work
without sign-in; agent runs require a valid session.

### 3. Manual authentication (if not using quickstart)

Pick **one** path:

```bash
# Create account + org (email)
teardrop auth signup --email you@example.com --org-name acme

# Wallet-first SIWE (generate a wallet on first run)
teardrop auth login --siwe --generate-wallet

# SIWE with an existing key file (key is read once; not persisted unless --save-key)
teardrop auth login --siwe --key-file ./wallet.key

# Existing email account
teardrop auth login --email you@example.com

# Pre-issued JWT / M2M
teardrop auth login --token <jwt>
teardrop auth login --client-id <id> --client-secret <secret>
```

Private keys are never written to disk unless the user explicitly passes
`--save-key` (OS keyring only; plaintext keyring backends are refused).

### 4. Verify session

```bash
teardrop auth status
teardrop auth status --json
```

Expect exit code `0` and a resolved identity/org. On failure, re-run login.

### 5. Credential precedence (do not fight env vars)

Env credentials override interactive sessions. Precedence: `TEARDROP_API_KEY` →
`TEARDROP_EMAIL`+`TEARDROP_SECRET` → `TEARDROP_CLIENT_ID`+`TEARDROP_CLIENT_SECRET` →
system keyring → `access_token` in `~/.teardrop/config.toml`. Unset/update stale env
credentials before retrying interactive login.

### 6. Sign out when requested

```bash
teardrop auth logout
```

Logout revokes the refresh token, clears stored credentials, and clears the
active chat thread id.

## Reference

- CLI reference — Authentication: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#authentication
- CLI reference — Exit codes: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#exit-codes
- README quickstart: https://github.com/teardrop-ai/teardrop-cli/blob/main/README.md

## Troubleshooting

| Symptom | Recovery |
|---------|----------|
| `teardrop` not found | Reinstall: `pip install teardrop-skills` (includes `teardrop-cli`). If installed into a venv, the binary may be in `venv/Scripts/` (Windows) or `venv/bin/` (POSIX) — check there and add it to PATH or invoke it directly. |
| Auth fails with env set | Unset stale `TEARDROP_*` vars; env credentials take precedence over interactive login |
| SIWE / keyring errors | Do not use plaintext keyring fallbacks; omit `--save-key` unless an encrypted backend is available |
| Signup rejected | Password must be ≥ 8 chars with ≥ 1 digit; org name 1–200 chars; rate limit 3 signups/min/email |
| Exit code `1` | Auth, rate limit, or API error — inspect stderr and retry after fixing credentials |
| Exit code `2` | Invalid input — fix flags/arguments and retry |

## Missing inputs & fallbacks

| Missing | Agent action |
|---------|--------------|
| No credentials at all | Run `teardrop auth login --siwe --generate-wallet` — zero-input SIWE creates a wallet and signs in automatically. No email or password needed. |
| Email given, no password | Run `teardrop auth signup --email <email> --org-name <org>` (interactive — prompts for password). If no org name, use `acme` or ask. |
| Email given, password given | Run `teardrop auth login --email <email>` (secret prompted interactively). |
| Org name missing for signup | Use the email local-part (before `@`) as org name, or ask the user. |
| `auth status` fails | Re-run login with the same method; check env vars (step 5). |

**Decision order:**
1. If user provided explicit credentials → use them.
2. If user said nothing → `--siwe --generate-wallet` (no input required).
3. If user said "I have an account" but no details → ask for email.

## Exit codes

- `0` — success
- `1` — error (auth, rate limit, API)
- `2` — invalid input
