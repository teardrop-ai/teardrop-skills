---
name: install
description: Install Teardrop CLI, authenticate, and complete first-time onboarding.
applyTo: "**/*"
---

## Purpose

Get a user from zero to a working Teardrop session: install the CLI, create or
sign into an account/org, verify identity, and optionally run the guided
quickstart. Use this skill whenever the user needs onboarding, login, signup,
session checks, or logout.

## Prerequisites

- Python ≥ 3.11
- Network access to PyPI and the Teardrop API
- For SIWE: ability to generate or supply an Ethereum private key (never commit keys)
- For email auth: a password ≥ 8 characters with ≥ 1 digit

## Workflow

### 1. Install the CLI

```bash
pip install teardrop-cli
teardrop --version
```

Exit code `0` confirms the binary is on `PATH`.

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

If login appears ignored, check environment credentials first — they override
interactive sessions:

1. `TEARDROP_API_KEY`
2. `TEARDROP_EMAIL` + `TEARDROP_SECRET`
3. `TEARDROP_CLIENT_ID` + `TEARDROP_CLIENT_SECRET`
4. System keyring
5. `access_token` in `~/.teardrop/config.toml`

Unset or update rejected env credentials before retrying interactive login.

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
| `teardrop` not found | Ensure install env is active; re-run `pip install teardrop-cli` and confirm `teardrop --version` |
| Auth fails with env set | Unset stale `TEARDROP_*` vars; env credentials take precedence over interactive login |
| SIWE / keyring errors | Do not use plaintext keyring fallbacks; omit `--save-key` unless an encrypted backend is available |
| Signup rejected | Password must be ≥ 8 chars with ≥ 1 digit; org name 1–200 chars; rate limit 3 signups/min/email |
| Exit code `1` | Auth, rate limit, or API error — inspect stderr and retry after fixing credentials |
| Exit code `2` | Invalid input — fix flags/arguments and retry |

## Exit codes

- `0` — success
- `1` — error (auth, rate limit, API)
- `2` — invalid input
