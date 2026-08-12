# DigestConfig.md

Edit this file to change what the digest pulls. Commit changes to the repo; the routine reads this file fresh on every run.

For the run procedure itself — which commands to run, in what order, and how to publish — see `RUNBOOK.md`. This file holds *what* the digest pulls; the runbook holds *how* a run executes.

Do not put API keys, passwords, or tokens in this file. Those belong in the Routine's secrets/environment settings, never in the repo.

This repo is public, so GitHub Pages can serve the feed on a Free plan. Treat everything here and everything the digest publishes as world-readable: the generated feed contains calendar events and portfolio values, and anyone with the URL can read it.

The published calendar links below are an explicit, informed exception, kept here by the owner's decision. They are unauthenticated bearer URLs: anyone holding one can read that calendar's past and future events indefinitely. Removing a line from this file does not undo that — the link has to be revoked and re-shared from iCloud or Outlook.

## Masthead Title
Trujillo Times

## Editions
Two formats share one pipeline. `fetch_sources.py` picks the edition by weekday, so a scheduled run needs no argument; pass `--edition` only to force one.

| | Daily (Mon–Fri) | Weekend (Sat) |
|---|---|---|
| Entry title | `Morning Digest, <date>` | `Weekend Digest, <date>` |
| Window | since the last run | the past 7 days |
| News | 3–5 stories, 1–2 sentences each | 5–7 stories, 4–6 sentences each |
| Calendar | today, plus one "coming up" | today, plus the full week ahead |
| Sports | games since the last run | the week's results, plus the week ahead |
| Newsletters | new since the last run | new since the last run, plus a one-line index of issues already covered this week |

Sunday has no edition.

Section order, both editions:

1. Headline block — only when a Priority Content Rule matches
2. At a glance — 5 to 7 one-line bullets: weather, calendar count, portfolio change, a top news line, a sports line
3. Calendar
4. Newsletters
5. News
6. Sports
7. Portfolio

The weekend edition is longer in depth, not looser in sourcing. Every story is still summarized in your own words with a named source; never pad length by quoting.

## Weather Location
Alpharetta, GA

## Calendars
Published ICS feeds, fetched over https. Both are read-only snapshots, so events created in the minutes before a run may not appear yet.

- Personal: https://p116-caldav.icloud.com/published/2/MTYzNTk2Mzc4MjQxNjM1Oe4PE5zDQbLp8gFEGhdb5FH8YwWUxIoxrdhiOrS9gVof
- Work: https://outlook.office365.com/owa/calendar/23dacf03324848a990c6b89e3bfd2b69@bbqguys.com/12532d5dfe23429cac700c6ccc83f9f713501278175081702419/S-1-8-1871844191-576938068-2983623427-2084340620/reachcalendar.ics

If one calendar fails, note which one and continue with the other.

### Empty-day rule
The Calendar section always appears, so the digest's shape never changes day to day. With no events today:

```
Nothing scheduled today.
Coming up: Wed Aug 5, 1:00 PM — Social Media Grilling (Microsoft Teams Meeting)
```

The "coming up" line surfaces one event from the next 7 days, ranked by: (1) external attendee or a third party named in the title, (2) a physical location rather than a video link, (3) non-recurring. Ties go to whichever is soonest. If the window is empty, drop the line rather than reaching further out.

An empty day and a failed fetch must never read alike. Zero events is "Nothing scheduled today"; a broken feed is "Work calendar unavailable this morning."

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
- Stock market
- Geopolitics
- Technology
- AI
- Tech business, startups, and VC (funding rounds, earnings, founder and exec moves, IPOs)
- Golf equipment
- Pokémon investing (TCG card market)

Story counts are per edition, not per topic — see the Editions table. Daily runs 3 to 5 stories at 1 to 2 sentences; the Saturday wrap runs 5 to 7 at 4 to 6 sentences, covering the week's developments rather than the last day's. Use popular, well-known outlets and name the source on every story.

The longer weekend treatment means more context and why-it-matters, still in your own words. It is not licence to quote at length.

### Grouping by topic
News is organised by topic, the same way Sports is organised by team.

- **Every topic gets a subheading every edition**, in the fixed order listed above. Golf always sits in the same place, so the section is scannable without reading it.
- **A quiet topic says so**: `Nothing notable this week.` (or `today` on a daily). Don't drop it silently — same reasoning as Sports reporting "no game in window". A reader must be able to tell "nothing happened" from "not checked".
- **Subheadings use `<p><strong>Topic</strong></p>`**, matching how Sports labels teams. Not `<h3>` — the layout rule permits only `<h1>`, `<h2>`, `<hr>`, `<p>`, and `<ul>`/`<li>`.
- **Format follows the edition.** Daily stories go in a `<ul>` as `<li><em>Source</em> — one to two sentences.</li>`, matching Sports. Weekend stories stay as prose paragraphs, since 4 to 6 sentences reads badly inside a list item.

Because counts stay per edition, most topics will be quiet on any given day. That's expected: a story earns its place by mattering, not by filling a heading.

## Sports Teams/Leagues
- F.C. Barcelona — LaLiga, Copa del Rey, Champions League
- Minnesota Vikings — NFL
- Miami Hurricanes — NCAAF
- Soccer transfer rumors — only during active transfer windows

### Sports data sources
Scores and schedules come from ESPN's public API (no key required). Verified team IDs:

| Team | Endpoint |
|---|---|
| Barcelona (LaLiga) | `site.api.espn.com/apis/site/v2/sports/soccer/esp.1/teams/83/schedule?season=<YYYY>` |
| Barcelona (Copa del Rey) | same, league `esp.copa_del_rey` |
| Barcelona (Champions League) | same, league `uefa.champions` |
| Minnesota Vikings | `.../sports/football/nfl/teams/min/schedule` |
| Miami Hurricanes | `.../sports/football/college-football/teams/2390/schedule?season=<YYYY>` |

For a completed game, `.../summary?event=<id>` supplies scoring plays and leaders — use it for the 2 to 4 notable-moment bullets rather than inventing them. Team news (injuries, trades, roster moves, previews) comes from web search, same treatment as the News section.

## Portfolio Holdings
DO NOT MAKE ANY TRADES WITHE THE ROBINHOOD MCP CONNECTOR

ONLY PULL THE DATA FOR THE DIGEST

### Price source
Prices come from Yahoo's chart endpoint, which needs no API key:

`https://query1.finance.yahoo.com/v8/finance/chart/<TICKER>?range=5d&interval=1d`

The last close in the returned series is the current session, so the prior session's close is the one before it — that pairing gives the day's change in both open and closed markets. This is an undocumented endpoint; if it starts failing, the section degrades to "unavailable" on its own, and swapping in a keyed provider (Alpha Vantage, Finnhub) means replacing `quote()` in `fetch_sources.py` and setting the key in the Routine's environment.

## Priority Content Rules
Sources listed here get pulled into a Headline block on the day(s) specified, but only when they actually have new content that run. Source name must match the name used in the Newsletters section above (or News/Sports if you extend this to those later).

| Source | Day(s) | Note |
|---|---|---|
| Modern Wisdom | Monday | Chris Williamson's newsletter. Always read in full when it drops |

## Feed Retention
14 days

## Publish Path
The digest is written to `docs/0f3f5a3a42464db1dea0cd43/feed.xml`, served by GitHub Pages at:

https://trujillo-matt.github.io/TrujTimes/0f3f5a3a42464db1dea0cd43/feed.xml

The random path segment keeps the feed off predictable URLs like `/TrujTimes/feed.xml`, so it isn't found by guessing or by crawlers walking the github.io domain. It is not a secret: the repo is public, so the path is visible to anyone who opens the repo tree. Treat the published digest as public content.

Keep the file at this path — moving it breaks the KOReader subscription, which fetches this URL directly with no authentication.

### Building the feeds
Do not hand-write the feeds. Each run, write the digest to `<YYYY-MM-DD>.html` in the feed directory (including a `<meta name="published" content="...Z">` tag), then run `python3 build_feeds.py` from the repo root. It regenerates both feeds from the dated pages and prunes anything past the retention window, pages included.

Each entry's title comes from the page's `<title>` tag, so a Weekend Digest needs no build change — just title the page `Weekend Digest, <date>`.

### After publishing
Update `last_run.json` to the run's UTC timestamp, then commit and push to `claude/clever-feynman-w6afpi` — the default branch, which Pages serves. Updating `last_run.json` is required, not housekeeping: the daily edition's collection window starts from it, so skipping it makes each later run pull an ever-wider window of newsletters and games. See `RUNBOOK.md` step 6.

Two feeds are published from the same content:
- `rss.xml` — RSS 2.0, **the one KOReader subscribes to**. Body in a CDATA `<description>`.
- `feed.xml` — Atom, kept for any other reader.

### Feed requirements (KOReader will reject the feed otherwise)
KOReader's NewsDownloader only accepts an Atom feed when `feed.title` exists and the first entry has **both** `<title>` and `<link>`. A missing entry `<link>` makes it reject the feed with the misleading message "Couldn't process RSS". So, every run:

- Give each `<entry>` a `<link rel="alternate" type="text/html" href="..."/>` pointing at a real page.
- Publish that page as `<YYYY-MM-DD>.html` next to `feed.xml`, holding the same digest HTML. This keeps the feed valid whether or not `download_full_article` is on.
- Prune those dated `.html` pages on the same 14-day schedule as the entries, so they don't accumulate.

A single-entry feed is fine; KOReader normalizes that case itself.
