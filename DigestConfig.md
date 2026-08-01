# DigestConfig.md

Edit this file to change what the digest pulls. Commit changes to the repo; the routine reads this file fresh on every run.

Do not put API keys, passwords, or tokens in this file. Those belong in the Routine's secrets/environment settings, never in the repo. Published calendar links count as tokens: the URL alone grants full read access.

This repo is public, so GitHub Pages can serve the feed on a Free plan. Treat everything here and everything the digest publishes as world-readable: the generated feed contains calendar events, to-dos, portfolio values, and health data, and anyone with the URL can read it. Secrets belong in the Routine's environment, never in a tracked file.

## Masthead Title
Trujillo Times

## Weather Location
Alpharetta, GA

## Calendars
Both calendars are published ICS links that need no authentication — the URL itself is the credential, so it lives in the Routine's secrets, not in this file. Set these two environment variables in the Routine settings:

- Personal: `$PERSONAL_CALENDAR_ICS` — iCloud published calendar (webcal:// URL; fetch it as https://)
- Work: `$WORK_CALENDAR_ICS` — Outlook/Office 365 published calendar (reachcalendar.ics URL)

If either variable is unset, that calendar is skipped and noted as unavailable in the digest.

## Newsletters (Atom/RSS feeds)
Kill the Newsletter feeds are email newsletters forwarded to an Atom feed. The rest are ordinary site RSS feeds. Both are fetched the same way.

Email newsletters (via Kill the Newsletter):
- Modern Wisdom: https://kill-the-newsletter.com/feeds/ycvwm3h1o2ykk5gdaxaw.xml
- Hurly: https://kill-the-newsletter.com/feeds/l14wu2ducssqo9sypirz.xml
- Watches of Espionage: https://kill-the-newsletter.com/feeds/l7ib22uj2wu22yobclps.xml
- 3-2-1 Thursday: https://kill-the-newsletter.com/feeds/ckq1cu7nzerpwdda277b.xml
- Kingdom: The Turn: https://kill-the-newsletter.com/feeds/0czbq4josh4gmwzgo9i1.xml

Site feeds:
- The Art of Manliness: https://artofmanliness.com/rss/
- Palladium: https://www.palladiummag.com/feed/
- The Verge: https://theverge.com/rss/index.xml
- ByteDrum: https://www.bytedrum.com/rss.xml
- Bless This Stuff: https://blessthisstuff.com/rss
- Cool Material: https://coolmaterial.com/feed/
- Uncrate: https://feeds.feedburner.com/uncrate

## News Topics/Sources
- [topic or source]
- [topic or source]

## Sports Teams/Leagues
- [F.C. Barcelona — LaLiga, Copa Del Rey, Champions League]
- [Minnesota Vikings — NFL]
- [Miami Hurricanes — NCAAF]
- Soccer Transfer Rumors [ONLY During active transfer windows]

## Portfolio Holdings
Manual entry only. This drives price lookups, not brokerage access.

| Ticker | Shares |
|---|---|
| | |

## Priority Content Rules
Sources listed here get pulled into a Headline block on the day(s) specified, but only when they actually have new content that run. Source name must match the name used in the Newsletters section above (or News/Sports if you extend this to those later).

| Source | Day(s) | Note |
|---|---|---|
| Modern Wisdom | Monday | Chris Williamson's newsletter. Always read in full when it drops |

## Reminders List
[list name, or leave blank for the default list]

## Feed Retention
14 days

## Publish Path
The digest is written to `docs/0f3f5a3a42464db1dea0cd43/feed.xml`, served by GitHub Pages at:

https://trujillo-matt.github.io/TrujTimes/0f3f5a3a42464db1dea0cd43/feed.xml

The random path segment keeps the feed off predictable URLs like `/TrujTimes/feed.xml`, so it isn't found by guessing or by crawlers walking the github.io domain. It is not a secret: the repo is public, so the path is visible to anyone who opens the repo tree. Treat the published digest as public content.

Keep the file at this path — moving it breaks the KOReader subscription, which fetches this URL directly with no authentication.

### Building the feeds
Do not hand-write the feeds. Each run, write the digest to `<YYYY-MM-DD>.html` in the feed directory (including a `<meta name="published" content="...Z">` tag), then run `python3 build_feeds.py` from the repo root. It regenerates both feeds from the dated pages and prunes anything past the retention window, pages included.

Two feeds are published from the same content:
- `rss.xml` — RSS 2.0, **the one KOReader subscribes to**. Body in a CDATA `<description>`.
- `feed.xml` — Atom, kept for any other reader.

### Feed requirements (KOReader will reject the feed otherwise)
KOReader's NewsDownloader only accepts an Atom feed when `feed.title` exists and the first entry has **both** `<title>` and `<link>`. A missing entry `<link>` makes it reject the feed with the misleading message "Couldn't process RSS". So, every run:

- Give each `<entry>` a `<link rel="alternate" type="text/html" href="..."/>` pointing at a real page.
- Publish that page as `<YYYY-MM-DD>.html` next to `feed.xml`, holding the same digest HTML. This keeps the feed valid whether or not `download_full_article` is on.
- Prune those dated `.html` pages on the same 14-day schedule as the entries, so they don't accumulate.

A single-entry feed is fine; KOReader normalizes that case itself.
