# DigestConfig.md

Edit this file to change what the digest pulls. Commit changes to the repo; the routine reads this file fresh on every run.

Do not put API keys, passwords, or tokens in this file. Those belong in the Routine's secrets/environment settings, never in the repo.

## Masthead Title
Trujillo Times

## Weather Location
Alpharetta, GA

## Calendars
- Personal: [calendar ID or account]
- Work: [calendar ID or account]

## Newsletters (Kill the Newsletter Atom feeds)
- [Newsletter name]: [feed URL]
- [Newsletter name]: [feed URL]

## News Topics/Sources
- [topic or source]
- [topic or source]

## Sports Teams/Leagues
- [team — league]
- [team — league]

## Portfolio Holdings
Manual entry only. This drives price lookups, not brokerage access.

| Ticker | Shares |
|---|---|
| | |

## Priority Content Rules
Sources listed here get pulled into a Headline block on the day(s) specified, but only when they actually have new content that run. Source name must match the name used in the Newsletters section above (or News/Sports if you extend this to those later).

| Source | Day(s) | Note |
|---|---|---|
| Chris Williamson newsletter | Monday | Always read in full when it drops |

## Reminders List
[list name, or leave blank for the default list]

## Feed Retention
14 days
