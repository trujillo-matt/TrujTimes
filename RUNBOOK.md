# RUNBOOK — Trujillo Times morning digest

The complete procedure for one run. Written for a session starting cold with no
prior context: everything needed is here or in `DigestConfig.md`.

Run every command from the repo root.

---

## 0. Preflight

Do this before any collection work. A run that can't publish should find out in
the first ten seconds and say so, not after an hour of work.

Run each of these as its own command. Keep `cd` on a line by itself rather than
chaining it with `&&` or `||` — the working directory persists between commands,
and a compound command containing `cd` can trigger a permission prompt that an
unattended run has nobody to answer.

```bash
cd /home/user/TrujTimes
```

```bash
ls DigestConfig.md fetch_sources.py build_feeds.py record_run.py
```

```bash
git rev-parse --abbrev-ref HEAD
```

```bash
git push --dry-run origin claude/clever-feynman-w6afpi
```

All four must succeed:

- If `cd` fails, there may be no clone at all in this session. The repo is
  public, so `git clone https://github.com/trujillo-matt/TrujTimes.git` works —
  but read the push note below before assuming the run can publish.
- If the `ls` doesn't list all four files, you're in the wrong directory.
- If `HEAD` isn't `claude/clever-feynman-w6afpi`, switch to it. That's the
  default branch and the one Pages serves.
- If `--dry-run` fails, see the push-access note below. If neither path works,
  the run has no way to publish. **Stop there** and say exactly that in the run
  log — don't write a digest that can't be delivered.

### Push access in a scheduled session

This is the known failure mode. A Routine carries a list of repositories that
get cloned at the start of each run. If that list is empty, the session starts
with no checkout and no scoped git credential: `no repo checkout found`, and any
push returns *"not in session's authorized set."* A week of scheduled runs
failed here silently before it was diagnosed.

The fix is to attach `trujillo-matt/TrujTimes` to the Routine — see `SETUP.md`.
Once attached, the plain `git push -u origin claude/clever-feynman-w6afpi` in
step 6 works, because pushes to `claude/`-prefixed branches are always accepted.

If the preflight push check fails, **stop and report it**. Do not reach for a
token or any other credential to work around it: cloud environments have no
secrets store, and the missing piece is the repository attachment, not
reachability.

A second thing can block a run even with the repo attached: the environment's
network access level. On **Trusted**, only a default allowlist is reachable and
the digest's sources are not on it — fetches fail with `403` and
`x-deny-reason: host_not_allowed`. That surfaces as several sources reporting
"unavailable" at once. `SETUP.md` lists the domains to allow.

---

## 1. Orient

Read `DigestConfig.md` first. It is authoritative for every value — masthead,
weather location, calendars, newsletter feeds, news topics, teams, holdings,
priority rules — and for the edition rules, section order, and formatting.

Do not invent values that aren't in it. If something isn't configured, the
section says so; it does not get filled in from memory.

---

## 2. Collect the mechanical sources

```bash
python3 fetch_sources.py
```

Emits one JSON document covering weather, calendars, newsletters, sports, and
portfolio. It picks the edition by weekday on its own — `weekend` on Saturday,
`daily` otherwise — so pass no arguments on a scheduled run. Use
`--edition daily|weekend` only to force one deliberately.

Every source carries `"status": "ok"` or `"status": "unavailable"` with a
reason. **An unavailable source becomes a short plain note in its own section
of the digest and nothing more.** It never halts the run, never surfaces as an
error, and never appears as a stack trace or error code in reader-facing text.
"Weather unavailable this morning" is the right register.

A source returning zero results is not a failure and must not read like one.
Zero calendar events is "Nothing scheduled today"; a calendar that failed to
fetch is "Work calendar unavailable this morning." A reader must always be able
to tell "nothing happened" from "not checked."

---

## 3. Gather the judgment parts

These need summarizing and selection, so they aren't scripted:

- **Newsletters** — `fetch_sources.py` returns entries new since the last run.
  Summarize each in 2–3 sentences in your own words. On the weekend edition it
  also returns `earlier_this_week`: issues already covered by a weekday
  edition, which get indexed by title in one line, not re-summarized.
- **News** — search for current stories on the configured topics. Story counts,
  sentence lengths, topic grouping, topic order, and the handling of quiet
  topics are all specified in `DigestConfig.md`.
- **Sports** — `fetch_sources.py` returns completed games and, on the weekend,
  upcoming fixtures. For a completed game, fetch the `summary_endpoint` it
  provides for real scoring plays and leaders to build the 2–4 notable-moment
  bullets. Also search for team news (injuries, trades, roster moves,
  previews), presented like News stories with a named source.
- **Portfolio** — if the `Robinhood Trading MCP` connector is available and
  enabled, call it for current positions and current value (see the
  read-only allowlist under Hard rules) and use that in place of
  `fetch_sources.py`'s portfolio block for this run. If the connector isn't
  available, isn't enabled in this session, times out, or returns anything
  incomplete or that doesn't look right, don't retry or guess at the
  missing piece — fall back to `fetch_sources.py`'s output (the manually
  maintained table in `DigestConfig.md` priced via Yahoo) for the whole
  section, same as before this connector existed. Never mix a live figure
  from one source with a stale one from the other in the same run. Either
  way, never write anything back to `DigestConfig.md`'s table — that file
  stays a human-edited fallback, not a cache for live data.

Name a source on every news and sports story.

---

## 4. Write the digest

Write to `docs/0f3f5a3a42464db1dea0cd43/<YYYY-MM-DD>.html`.

Two things are load-bearing:

- `<title>Morning Digest, <date></title>` on weekdays, `Weekend Digest, <date>`
  on Saturday. `build_feeds.py` takes each entry's title from this tag.
- `<meta name="published" content="<YYYY-MM-DDTHH:MM:SSZ>">` in the head.
  `build_feeds.py` reads it for entry timestamps and for pruning; the build
  fails without it.

Layout is a single linear column of semantic HTML only: `<h1>`, `<h2>`, `<hr>`,
`<p>`, `<ul>`/`<li>`. No floats, no grid, no multi-column, no tables, no inline
images, no `<h3>`. KOReader re-flows the page at the reader's own font size, so
anything positional is flattened unpredictably. Subheadings within a section
use `<p><strong>Label</strong></p>` — that's how Sports labels teams and News
labels topics.

Section order and the at-a-glance bullet set are in `DigestConfig.md`. Include
every section every edition, using a one-line note where a section has nothing,
so the shape of the digest never changes day to day.

---

## 5. Build the feeds

```bash
python3 build_feeds.py
```

Regenerates `feed.xml` (Atom) and `rss.xml` (RSS 2.0) from the dated pages and
prunes anything past 14 days, pages included. Never hand-write either feed.

KOReader subscribes to `rss.xml` and rejects a feed whose first item lacks
either a title or a link — it reports that as the misleading "Couldn't process
RSS". `build_feeds.py` handles this correctly; the failure mode only returns if
someone edits a feed by hand.

---

## 6. Record and publish

```bash
python3 record_run.py
git add -A
git commit -m "Publish digest for <date>"
git push -u origin claude/clever-feynman-w6afpi
```

**Updating `last_run.json` is not optional.** The daily edition's collection
window starts from it, so skipping the update makes every subsequent run pull a
wider and wider window of newsletters and games.

Note the shape of that first command. Anything that writes a file goes through
a committed script, never an inline `python3 -c "...open(...,'w')..."` or a
heredoc — inline interpreter writes can trip the permission classifier, and an
unattended run has nobody to approve the prompt. If you need a new write step,
add a script and commit it.

`claude/clever-feynman-w6afpi` is the repo's default branch and the one GitHub
Pages serves. Pages takes a minute or two to rebuild after a push.

Feed URL: https://trujillo-matt.github.io/TrujTimes/0f3f5a3a42464db1dea0cd43/rss.xml

---

## 7. Run log

Close with a short summary for session review, not part of the feed: which
sections succeeded, which were unavailable and why, and the feed URL.

---

## Hard rules

- **Never fabricate.** Not a data point, headline, score, highlight, or summary.
  An unavailable source is reported as unavailable, never filled in.
- **Never quote** newsletter or news content beyond a short attributed phrase.
- **Robinhood, if connected, is read-only and for exactly two things:**
  current positions (ticker + share count) and current position/account
  value. Nothing else. This is an allowlist, not a blocklist: if a call isn't
  fetching one of those two things, don't make it, regardless of how safe the
  tool's name or description makes it sound. In particular, never call
  anything that places, cancels, or modifies an order, moves money
  (transfer/deposit/withdrawal), or changes account settings or watchlists —
  those tools can live on the same connector. See "Portfolio" in step 3 for
  how the pulled data is used and when it falls back.
- **No other brokerage access.** No logins, no other brokerage APIs, no
  scraping, outside the one allowlisted Robinhood read.
- **Never store brokerage account numbers, statements, or personal details in
  this repo.** Ticker, share count, and value are fine to publish; nothing
  else from the account is.
- **Never commit secrets or personal data.** The repo is public. Ticker and
  share count are fine; account numbers, statements, names, and addresses are
  not.
- **A source failure is never a run failure.**

---

## Schedule

One Routine fires this runbook at 5:30 AM ET, Monday through Saturday. Sunday
has no edition.

The cron is `30 9 * * 1-6` in UTC, which is 5:30 AM Eastern **during daylight
saving**. When ET returns to EST in early November, this fires at 4:30 AM
local; correcting it means changing the cron to `30 10 * * 1-6`, and reversing
that in March.
