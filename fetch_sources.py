#!/usr/bin/env python3
"""Collect the mechanical digest sources and emit one JSON document.

Every source is wrapped: a failure, timeout, or auth error becomes
{"status": "unavailable", "reason": "..."} for that source alone. Nothing
raises past main(), so one dead source can never halt a run. Summarizing and
story selection happen outside this script; it only gathers facts.

Two editions share this pipeline. The daily edition (Mon-Fri) collects since
the last run; the weekend edition (Sat) looks back a full week and forward a
full week, for a wrap rather than another daily. Edition defaults by weekday,
so a scheduled run needs no argument.

Usage:  python3 fetch_sources.py [--edition daily|weekend]
                                 [--config DigestConfig.md] [--state last_run.json]
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
UA = "TrujTimes-digest/1.0 (matt.truj7@gmail.com)"
TIMEOUT = 25
LOOKAHEAD_DAYS = 7
WEEK_DAYS = 7

NWS_GRID = "https://api.weather.gov/gridpoints/FFC/53,101/forecast"
NWS_ALERTS = "https://api.weather.gov/alerts/active?point=34.0754,-84.2941"
ESPN = "https://site.api.espn.com/apis/site/v2/sports"

TEAMS = [
    {"name": "F.C. Barcelona", "sport": "soccer", "leagues":
        ["esp.1", "esp.copa_del_rey", "uefa.champions"], "id": "83", "seasoned": True},
    # ESPN's schedule endpoint returns regular season by default; preseason
    # games only appear under seasontype=1, so query both and merge.
    {"name": "Minnesota Vikings", "sport": "football", "leagues": ["nfl"],
     "id": "min", "seasoned": False, "season_types": [1, 2]},
    {"name": "Miami Hurricanes", "sport": "football", "leagues": ["college-football"],
     "id": "2390", "seasoned": True},
]

VIDEO_HINTS = ("teams meeting", "zoom", "google meet", "webex", "microsoft teams")

# Exchange publishes TZIDs as Windows zone names ("Eastern Standard Time"),
# which ZoneInfo cannot resolve. These names include DST despite the "Standard".
WINDOWS_TZ = {
    "Eastern Standard Time": "America/New_York",
    "Central Standard Time": "America/Chicago",
    "Mountain Standard Time": "America/Denver",
    "US Mountain Standard Time": "America/Phoenix",
    "Pacific Standard Time": "America/Los_Angeles",
    "Alaskan Standard Time": "America/Anchorage",
    "Hawaiian Standard Time": "Pacific/Honolulu",
    "Atlantic Standard Time": "America/Halifax",
    "GMT Standard Time": "Europe/London",
    "W. Europe Standard Time": "Europe/Berlin",
    "Romance Standard Time": "Europe/Paris",
    "Central Europe Standard Time": "Europe/Budapest",
    "UTC": "UTC",
}


# --------------------------------------------------------------------------
# fetching


# ESPN returns 403 for our identifying User-Agent (and for Mozilla-style ones),
# but serves the library default fine. NWS's API terms ask for a contact string,
# so the identifying UA stays everywhere else.
NO_UA_HOSTS = ("site.api.espn.com",)


def fetch(url, retries=1):
    """GET a URL as bytes. One retry for anything transient."""
    host = urllib.parse.urlsplit(url).hostname or ""
    headers = {} if host in NO_UA_HOSTS else {"User-Agent": UA}
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001 - any failure is just "unavailable"
            last = exc
            if attempt < retries:
                time.sleep(2)
    raise last


def guard(fn, *args, **kwargs):
    """Run a collector, converting any failure into an unavailable marker."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "reason": short_reason(exc)}


def short_reason(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP {exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return f"network error ({exc.reason})"
    text = str(exc).strip() or exc.__class__.__name__
    return text[:120]


# --------------------------------------------------------------------------
# config


def parse_config(path):
    """Pull the values the collectors need out of DigestConfig.md."""
    text = open(path, encoding="utf-8").read()

    def section(name):
        m = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        return m.group(1) if m else ""

    cal = {}
    for label, url in re.findall(r"^- (Personal|Work):\s*(https?://\S+)", section("Calendars"), re.M):
        cal[label.lower()] = url

    feeds = re.findall(r"^- (.+?):\s*(https?://\S+)", section("Newsletters (Atom/RSS feeds)"), re.M)

    holdings = []
    for row in re.findall(r"^\|\s*([A-Za-z.\-]+)\s*\|\s*([\d.]+)\s*\|", section("Portfolio Holdings"), re.M):
        if row[0].lower() != "ticker":
            holdings.append({"ticker": row[0].upper(), "shares": float(row[1])})

    return {"calendars": cal, "feeds": feeds, "holdings": holdings}


def load_state(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:  # noqa: BLE001 - a missing/corrupt state file is not fatal
        return {}


def window_start(state):
    """Start of the 'since last run' window; falls back to 24h."""
    raw = (state or {}).get("last_run")
    if raw:
        try:
            return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc) - timedelta(days=1)


def default_edition():
    """Saturday runs the weekend wrap; every other day is a daily."""
    return "weekend" if datetime.now(TZ).weekday() == 5 else "daily"


# --------------------------------------------------------------------------
# weather


def get_weather():
    data = json.loads(fetch(NWS_GRID))
    periods = data["properties"]["periods"][:2]
    out = []
    for p in periods:
        out.append({
            "name": p["name"],
            "temperature": f'{p["temperature"]}°{p["temperatureUnit"]}',
            "precip_chance": (p.get("probabilityOfPrecipitation") or {}).get("value"),
            "forecast": p["shortForecast"],
            "detail": p.get("detailedForecast", ""),
        })

    alerts = []
    try:
        for f in json.loads(fetch(NWS_ALERTS)).get("features", []):
            alerts.append({"event": f["properties"].get("event"),
                           "headline": f["properties"].get("headline")})
    except Exception:  # noqa: BLE001 - forecast alone is still worth publishing
        alerts = None

    return {"status": "ok", "periods": out,
            "alerts": alerts if alerts is not None else [],
            "alerts_checked": alerts is not None}


# --------------------------------------------------------------------------
# calendar


def unfold(raw):
    """Undo RFC 5545 line folding."""
    return raw.replace("\r\n", "\n").replace("\r", "\n").replace("\n ", "").replace("\n\t", "")


def ics_value(text):
    """Decode the escapes iCalendar puts in TEXT values."""
    return (text.replace("\\,", ",").replace("\\;", ";")
                .replace("\\n", " ").replace("\\N", " ").replace("\\\\", "\\").strip())


def parse_dt(prop, value):
    """Return (datetime|date, is_all_day) in local time."""
    if len(value) == 8 and value.isdigit():
        return date(int(value[:4]), int(value[4:6]), int(value[6:8])), True
    tz = TZ
    m = re.search(r"TZID=([^;:]+)", prop)
    if m:
        name = m.group(1).strip().strip('"')
        try:
            tz = ZoneInfo(WINDOWS_TZ.get(name, name))
        except Exception:  # noqa: BLE001 - unknown zone, fall back to local
            tz = TZ
    if value.endswith("Z"):
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=tz)
    return dt.astimezone(TZ), False


def expand_recurrence(start, rrule, horizon_end):
    """Expand the simple DAILY/WEEKLY/MONTHLY/YEARLY cases within the horizon.

    Deliberately shallow: enough for the today + 7-day windows this script
    reports, not a general RRULE engine. BYDAY and friends are ignored, so an
    unusual rule simply yields its base occurrence.
    """
    parts = dict(p.split("=", 1) for p in rrule.split(";") if "=" in p)
    freq = parts.get("FREQ")
    if freq not in {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}:
        return [start]
    interval = int(parts.get("INTERVAL", 1) or 1)
    until = None
    if parts.get("UNTIL"):
        try:
            until, _ = parse_dt("", parts["UNTIL"])
        except Exception:  # noqa: BLE001
            until = None

    step = {"DAILY": timedelta(days=interval), "WEEKLY": timedelta(weeks=interval),
            "MONTHLY": timedelta(days=30 * interval), "YEARLY": timedelta(days=365 * interval)}[freq]

    out, cur, guard_count = [], start, 0
    while guard_count < 500:
        as_dt = cur if isinstance(cur, datetime) else datetime.combine(cur, datetime.min.time(), TZ)
        if as_dt > horizon_end:
            break
        if until is not None:
            u = until if isinstance(until, datetime) else datetime.combine(until, datetime.min.time(), TZ)
            if as_dt > u:
                break
        out.append(cur)
        cur = cur + step
        guard_count += 1
    return out or [start]


def parse_ics(raw, horizon_end):
    """Return event dicts occurring on or before horizon_end."""
    events = []
    for block in re.findall(r"BEGIN:VEVENT\n(.*?)END:VEVENT", unfold(raw), re.S):
        fields = {}
        for line in block.split("\n"):
            if ":" not in line:
                continue
            prop, _, value = line.partition(":")
            fields.setdefault(prop.split(";")[0], []).append((prop, value))

        if "DTSTART" not in fields or "SUMMARY" not in fields:
            continue
        prop, value = fields["DTSTART"][0]
        try:
            start, all_day = parse_dt(prop, value)
        except Exception:  # noqa: BLE001 - skip an event we can't place in time
            continue

        starts = [start]
        if "RRULE" in fields:
            starts = expand_recurrence(start, fields["RRULE"][0][1], horizon_end)

        summary = ics_value(fields["SUMMARY"][0][1])
        location = ics_value(fields["LOCATION"][0][1]) if "LOCATION" in fields else ""
        attendees = len(fields.get("ATTENDEE", []))
        for s in starts:
            events.append({"summary": summary, "location": location, "start": s,
                           "all_day": all_day, "attendees": attendees,
                           "recurring": "RRULE" in fields})
    return events


def fmt_event(ev, source, with_date=False):
    if ev["all_day"]:
        when = "All day"
        stamp = ev["start"].isoformat()
    else:
        when = ev["start"].strftime("%-I:%M %p")
        stamp = ev["start"].isoformat()
    if with_date:
        d = ev["start"] if not ev["all_day"] else ev["start"]
        when = f'{d.strftime("%a %b %-d")}, {when}'
    return {"title": ev["summary"], "when": when, "location": ev["location"],
            "calendar": source, "start": stamp}


def rank_upcoming(ev):
    """Lower sorts first. Mirrors the heuristic documented in DigestConfig.md."""
    loc = (ev["location"] or "").lower()
    external = 0 if ev["attendees"] > 1 else 1
    physical = 0 if loc and not any(h in loc for h in VIDEO_HINTS) else 1
    one_off = 0 if not ev["recurring"] else 1
    return (external, physical, one_off, ev["start"].isoformat())


def get_calendars(urls, edition="daily"):
    today = datetime.now(TZ).date()
    horizon_end = datetime.combine(today + timedelta(days=LOOKAHEAD_DAYS),
                                   datetime.max.time(), TZ)

    today_events, upcoming, per_cal = [], [], {}
    for label in ("personal", "work"):
        url = urls.get(label)
        if not url:
            per_cal[label] = {"status": "unavailable", "reason": "no URL configured"}
            continue
        try:
            events = parse_ics(fetch(url).decode("utf-8", "replace"), horizon_end)
        except Exception as exc:  # noqa: BLE001
            per_cal[label] = {"status": "unavailable", "reason": short_reason(exc)}
            continue

        per_cal[label] = {"status": "ok", "events_parsed": len(events)}
        for ev in events:
            day = ev["start"].date() if isinstance(ev["start"], datetime) else ev["start"]
            if day == today:
                today_events.append((ev, label))
            elif today < day <= today + timedelta(days=LOOKAHEAD_DAYS):
                upcoming.append((ev, label))

    # Collapse exact duplicates - the work feed repeats some events verbatim.
    seen, deduped = set(), []
    for ev, label in sorted(today_events, key=lambda p: (p[0]["all_day"] is False, p[0]["start"].isoformat())):
        key = (ev["summary"], ev["start"].isoformat())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(fmt_event(ev, label))

    # Daily surfaces one look-ahead event; the weekend wrap lists the whole week.
    best, week_ahead = None, []
    if upcoming:
        ev, label = min(upcoming, key=lambda p: rank_upcoming(p[0]))
        best = fmt_event(ev, label, with_date=True)
    if edition == "weekend":
        seen_up = set()
        for ev, label in sorted(upcoming, key=lambda p: p[0]["start"].isoformat()):
            key = (ev["summary"], ev["start"].isoformat())
            if key in seen_up:
                continue
            seen_up.add(key)
            week_ahead.append(fmt_event(ev, label, with_date=True))

    ok = [k for k, v in per_cal.items() if v.get("status") == "ok"]
    return {"status": "ok" if ok else "unavailable",
            "reason": None if ok else "both calendars failed",
            "calendars": per_cal, "today": deduped, "coming_up": best,
            "week_ahead": week_ahead}


# --------------------------------------------------------------------------
# newsletters


def entry_time(node, ns):
    for tag in (f"{ns}updated", f"{ns}published", "pubDate"):
        raw = node.findtext(tag)
        if not raw:
            continue
        raw = raw.strip()
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
                    "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
            try:
                dt = datetime.strptime(raw, fmt)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def get_newsletters(feeds, since, edition="daily", fresh_since=None):
    """Split feed entries into unsummarized and already-covered.

    `fresh_since` is the last-run cutoff: anything after it has not appeared in
    a digest yet and needs summarizing. On the weekend it differs from `since`
    (the week boundary), so issues the weekday editions already covered land in
    earlier_this_week and are only indexed by title.
    """
    A = "{http://www.w3.org/2005/Atom}"
    fresh_since = fresh_since or since
    results, earlier, failures = [], [], []
    for name, url in feeds:
        try:
            root = ET.fromstring(fetch(url))
        except Exception as exc:  # noqa: BLE001
            failures.append({"name": name, "reason": short_reason(exc)})
            continue

        nodes = root.findall(f".//{A}entry") or root.findall(".//item")
        ns = A if root.findall(f".//{A}entry") else ""
        fresh, prior = [], []
        for n in nodes:
            ts = entry_time(n, ns)
            if ts is None:
                continue
            link = n.findtext("link") or ""
            if not link:
                el = n.find(f"{ns}link")
                link = el.get("href", "") if el is not None else ""
            if not link:
                guid = n.findtext("guid") or ""
                if guid.startswith("http"):
                    link = guid
            item = {"title": (n.findtext(f"{ns}title") or "").strip(),
                    "published": ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "link": link}
            if ts > fresh_since:
                fresh.append(item)
            elif edition == "weekend" and ts > since:
                # Already summarized in a weekday edition - the wrap only indexes these.
                prior.append(item)
        if fresh:
            results.append({"name": name, "entries": fresh[:5]})
        if prior:
            earlier.append({"name": name, "entries": prior[:5]})

    out = {"status": "ok", "since": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "with_new_content": results, "failed_feeds": failures}
    if edition == "weekend":
        out["earlier_this_week"] = earlier
    return out


# --------------------------------------------------------------------------
# sports


def parse_espn_date(raw):
    """ESPN mixes formats: '2026-08-15T17:00Z' and '...T17:00:00Z'.

    Both must parse. Getting this wrong silently drops events, which reads as
    'no game in window' rather than as an error.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def game_record(event, team_name):
    comp = (event.get("competitions") or [{}])[0]
    status = (comp.get("status") or event.get("status") or {}).get("type", {})
    scores = []
    for c in comp.get("competitors", []):
        scores.append({"team": c.get("team", {}).get("displayName"),
                       "abbrev": c.get("team", {}).get("abbreviation"),
                       "score": (c.get("score") or {}).get("displayValue")
                       if isinstance(c.get("score"), dict) else c.get("score"),
                       "home_away": c.get("homeAway")})
    return {"team": team_name, "event_id": event.get("id"), "name": event.get("name"),
            "date": event.get("date"), "completed": bool(status.get("completed")),
            "state": status.get("state"), "scores": scores}


def get_sports(since, edition="daily"):
    season = datetime.now(TZ).year
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=WEEK_DAYS) if edition == "weekend" else now
    out, failures = [], []
    for team in TEAMS:
        games, upcoming, any_ok = [], [], False
        # A team may need more than one call per league: NFL preseason lives
        # under seasontype=1 and is absent from the default response.
        calls = []
        for league in team["leagues"]:
            for stype in team.get("season_types", [None]):
                params = []
                if team["seasoned"]:
                    params.append(f"season={season}")
                if stype is not None:
                    params.append(f"seasontype={stype}")
                url = f'{ESPN}/{team["sport"]}/{league}/teams/{team["id"]}/schedule'
                if params:
                    url += "?" + "&".join(params)
                calls.append((league, url))

        seen_events = set()
        for league, url in calls:
            try:
                data = json.loads(fetch(url))
                any_ok = True
            except Exception as exc:  # noqa: BLE001
                failures.append({"team": team["name"], "league": league,
                                 "reason": short_reason(exc)})
                continue
            for ev in data.get("events", []):
                if ev.get("id") in seen_events:
                    continue
                seen_events.add(ev.get("id"))
                when = parse_espn_date(ev.get("date"))
                if when is None:
                    continue
                if since <= when <= now:
                    rec = game_record(ev, team["name"])
                    rec["league"] = league
                    if rec["completed"]:
                        rec["summary_endpoint"] = (
                            f'{ESPN}/{team["sport"]}/{league}/summary?event={rec["event_id"]}')
                    games.append(rec)
                elif now < when <= horizon:
                    rec = game_record(ev, team["name"])
                    rec["league"] = league
                    upcoming.append(rec)

        entry = {"team": team["name"],
                 "status": "ok" if any_ok else "unavailable",
                 "games": sorted(games, key=lambda g: g["date"] or ""),
                 "note": None if games else "no game in window"}
        if edition == "weekend":
            entry["upcoming"] = sorted(upcoming, key=lambda g: g["date"] or "")
        out.append(entry)

    return {"status": "ok", "since": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "teams": out, "failures": failures}


# --------------------------------------------------------------------------
# portfolio


QUOTE_URL = ("https://query1.finance.yahoo.com/v8/finance/chart/"
             "{ticker}?range=5d&interval=1d")


def quote(ticker):
    """Latest price and the prior session's close.

    Yahoo's chart endpoint needs no API key. The last close in the series is
    the current session (partial while the market is open, final after), so the
    prior close is always the one before it.
    """
    data = json.loads(fetch(QUOTE_URL.format(ticker=ticker)))
    result = data["chart"]["result"][0]
    meta = result["meta"]
    closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]
    price = meta.get("regularMarketPrice")
    if price is None and closes:
        price = closes[-1]
    prior = closes[-2] if len(closes) >= 2 else None
    if price is None:
        raise ValueError(f"no price for {ticker}")
    return float(price), (float(prior) if prior is not None else None)


def get_portfolio(holdings, api_key=None):
    if not holdings:
        return {"status": "unavailable", "reason": "no holdings configured"}

    rows, failed = [], []
    total = prior_total = 0.0
    for h in holdings:
        try:
            price, prior = quote(h["ticker"])
        except Exception as exc:  # noqa: BLE001 - one bad ticker must not sink the section
            failed.append({"ticker": h["ticker"], "reason": short_reason(exc)})
            continue
        value = price * h["shares"]
        total += value
        row = {"ticker": h["ticker"], "shares": h["shares"],
               "price": round(price, 2), "value": round(value, 2)}
        if prior is not None:
            row["prior_close"] = round(prior, 2)
            row["change_pct"] = round((price - prior) / prior * 100, 2)
            prior_total += prior * h["shares"]
        rows.append(row)

    if not rows:
        return {"status": "unavailable", "reason": "no prices returned",
                "failed": failed}

    out = {"status": "ok", "holdings": rows, "total_value": round(total, 2)}
    if prior_total:
        out["prior_total_value"] = round(prior_total, 2)
        out["change_value"] = round(total - prior_total, 2)
        out["change_pct"] = round((total - prior_total) / prior_total * 100, 2)
    if failed:
        out["failed"] = failed
    return out


# --------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", choices=("daily", "weekend"), default=None,
                    help="defaults to weekend on Saturday, daily otherwise")
    ap.add_argument("--config", default="DigestConfig.md")
    ap.add_argument("--state", default="last_run.json")
    args = ap.parse_args()

    edition = args.edition or default_edition()

    try:
        cfg = parse_config(args.config)
    except Exception as exc:  # noqa: BLE001 - without config there is nothing to collect
        json.dump({"error": f"could not read {args.config}: {short_reason(exc)}"}, sys.stdout)
        return 1

    now = datetime.now(timezone.utc)
    last_run = window_start(load_state(args.state))
    # The weekend wrap looks back a full week regardless of when the last run was,
    # but newsletters still key off last_run so covered issues aren't re-summarized.
    since = now - timedelta(days=WEEK_DAYS) if edition == "weekend" else last_run

    out = {
        "edition": edition,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local_date": datetime.now(TZ).strftime("%A, %B %-d, %Y"),
        "window_start": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "weather": guard(get_weather),
        "calendar": guard(get_calendars, cfg["calendars"], edition),
        "newsletters": guard(get_newsletters, cfg["feeds"], since, edition, last_run),
        "sports": guard(get_sports, since, edition),
        "portfolio": guard(get_portfolio, cfg["holdings"], None),
    }
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
