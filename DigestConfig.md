# DigestConfig.md

Edit this file to change what the digest pulls. Commit changes to the repo; the routine reads this file fresh on every run.

Do not put API keys, passwords, or tokens in this file. Those belong in the Routine's secrets/environment settings, never in the repo.

## Masthead Title
Trujillo Times

## Weather Location
Alpharetta, GA

## Calendars
- Personal: [webcal://p116-caldav.icloud.com/published/2/MTYzNTk2Mzc4MjQxNjM1Oe4PE5zDQbLp8gFEGhdb5FH8YwWUxIoxrdhiOrS9gVof ]
- Work: [calendar ID or account]

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
| Chris Williamson newsletter | Monday | Always read in full when it drops |

## Reminders List
[list name, or leave blank for the default list]

## Feed Retention
14 days
