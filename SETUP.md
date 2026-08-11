# SETUP — granting the scheduled run push access

The digest publishes by pushing to `claude/clever-feynman-w6afpi`, which GitHub
Pages serves. Everything else in the pipeline runs unattended; **this is the one
step that needs a human**, because it's an account settings change.

## The problem this solves

Sessions spawned by the Routine start with an empty authorized repository set.
They can clone the repo (it's public) but cannot push to it — the ambient git
credential doesn't cover `trujillo-matt/TrujTimes`. The push fails with
*"not in session's authorized set."*

This was diagnosed the hard way: roughly ten scheduled runs published nothing,
silently, over a week. Notifications are now enabled on the Routine, so a
failure reports itself rather than vanishing — but publishing stays blocked
until one of the options below is done.

Environment: **Default** — `env_016rCNuT4ogFkAwvJWc2zc9P` (`anthropic_cloud`).

Both options go through the same environment settings page. Option A is simpler
wherever it's available.

---

## Option A — authorize the repo for the environment (preferred)

Nothing expires, no secret to store or rotate.

1. Open <https://claude.ai/code> and go to environment settings for the
   **Default** environment.
2. Find the GitHub / repositories section for that environment.
3. Add **`trujillo-matt/TrujTimes`** to its repository set, with write access.
4. If the repo doesn't appear in the picker, the Claude GitHub App probably
   can't see it. On GitHub: **Settings → Applications → Claude → Configure**,
   then grant access to `TrujTimes` — either "All repositories" or add this one
   to the selected list — and retry step 3.

Docs: <https://code.claude.com/docs/en/claude-code-on-the-web>

No code changes follow. `RUNBOOK.md` step 6 already does a plain `git push`,
which starts working the moment the repo is authorized.

---

## Option B — `GH_TOKEN` environment variable (fallback)

Use only if Option A isn't available. `RUNBOOK.md` already documents the
fallback push, so nothing needs editing here either.

### B1. Create a fine-grained token

Works fine in a mobile browser.

1. GitHub → avatar → **Settings**
2. **Developer settings** (bottom of the left nav)
3. **Personal access tokens → Fine-grained tokens**
4. **Generate new token**
5. Name: `trujtimes-digest`
6. Resource owner: **trujillo-matt**
7. Expiration: 90 days is reasonable — but note it *will* expire, and the
   digest stops publishing that morning
8. Repository access: **Only select repositories → TrujTimes**
9. Permissions → Repository permissions → **Contents: Read and write**
   (sufficient on its own; grant nothing else)
10. **Generate token** and copy it — GitHub shows it exactly once

### B2. Add it to the environment

1. <https://claude.ai/code> → environment settings for **Default**
2. Add an environment variable named exactly **`GH_TOKEN`**, value = the token
3. Save

### Handling

Scope it to this one repo, keep `Contents: write` as its only permission, and
treat it as disposable. It lives in an environment that spawns unattended
sessions every morning, against a public repo. If it ever surfaces in a log,
revoke it rather than reusing it.

---

## Verifying

The next scheduled run is 5:30 AM ET, Monday–Saturday. To test sooner, fire the
Routine manually and watch for a commit on `claude/clever-feynman-w6afpi`
within a few minutes.

Success: a new dated page under `docs/0f3f5a3a42464db1dea0cd43/`, both feeds
rebuilt, and the deployed `rss.xml` still passing the KOReader gate.

Failure now reports itself — the Routine sends a completion notification by
push and email, and `RUNBOOK.md`'s step 0 preflight stops a run in the first
few seconds if it has no way to publish, rather than writing a whole digest
that can't be delivered.
