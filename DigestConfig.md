# DigestConfig.md

Edit this file to change what the digest pulls. Commit changes to the repo; the routine reads this file fresh on every run.

Do not put API keys, passwords, or tokens in this file. Those belong in the Routine's secrets/environment settings, never in the repo.

This repo is public, so GitHub Pages can serve the feed on a Free plan. Treat everything here and everything the digest publishes as world-readable: the generated feed contains calendar events, to-dos, portfolio values, and health data, and anyone with the URL can read it.

The published calendar links below are an explicit, informed exception, kept here by the owner's decision. They are unauthenticated bearer URLs: anyone holding one can read that calendar's past and future events indefinitely. Removing a line from this file does not undo that — the link has to be revoked and re-shared from iCloud or Outlook.

## Masthead Title
Trujillo Times

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

Pull **3 to 5 stories total per edition**, not per topic — chosen by what actually matters that day. Topics rotate in and out; a quiet topic simply doesn't appear. Use popular, well-known outlets and name the source on every story.

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
