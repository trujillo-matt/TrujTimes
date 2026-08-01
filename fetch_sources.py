#!/usr/bin/env python3
"""Collect the mechanical digest sources and emit one JSON document.

Every source is wrapped: a failure, timeout, or auth error becomes
{"status": "unavailable", "reason": "..."} for that source alone. Nothing
raises past main(), so one dead source can never halt a run. Summarizing and
story selection happen outside this script; it only gathers facts.

Usage:  python3 fetch_sources.py [--config DigestConfig.md] [--state last_run.json]
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
UA = "TrujTimes-digest/1.0 (matt.truj7@gmail.com)"
TIMEOUT = 25
LOOKAHEAD_DAYS = 7

NWS_GRID = "https://api.weather.gov/gridpoints/FFC/53,101/forecast"
NWS_ALERTS = "https://api.weather.gov/alerts/active?point=34.0754,-84.2941"
ESPN = "https://site.api.espn.com/apis/site/v2/sports"

TEAMS = [
    {"name": "F.C. Barcelona", "sport": "soccer", "leagues":
        ["esp.1", "esp.copa_del_rey", "uefa.champions"], "id": "83", "seasoned": True},
    {"name": "Minnesota Vikings", "sport": "football", "leagues": ["nfl"],
     "id": "min", "seasoned": False},
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


def fetch(url, retries=1):
    """GET a URL as bytes. One retry for anything transient."""
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
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


def get_calendars(urls):
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

    best = None
    if upcoming:
        ev, label = min(upcoming, key=lambda p: rank_upcoming(p[0]))
        best = fmt_event(ev, label, with_date=True)

    ok = [k for k, v in per_cal.items() if v.get("status") == "ok"]
    return {"status": "ok" if ok else "unavailable",
            "reason": None if ok else "both calendars failed",
            "calendars": per_cal, "today": deduped, "coming_up": best}


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


def get_newsletters(feeds, since):
    A = "{http://www.w3.org/2005/Atom}"
    results, failures = [], []
    for name, url in feeds:
        try:
            root = ET.fromstring(fetch(url))
        except Exception as exc:  # noqa: BLE001
            failures.append({"name": name, "reason": short_reason(exc)})
            continue

        nodes = root.findall(f".//{A}entry") or root.findall(".//item")
        ns = A if root.findall(f".//{A}entry") else ""
        fresh = []
        for n in nodes:
            ts = entry_time(n, ns)
            if ts is None or ts <= since:
                continue
            link = n.findtext("link") or ""
            if not link:
                el = n.find(f"{ns}link")
                link = el.get("href", "") if el is not None else ""
            fresh.append({"title": (n.findtext(f"{ns}title") or "").strip(),
                          "published": ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                          "link": link})
        if fresh:
            results.append({"name": name, "entries": fresh[:5]})

    return {"status": "ok", "since": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "with_new_content": results, "failed_feeds": failures}


# --------------------------------------------------------------------------
# sports


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


def get_sports(since):
    season = datetime.now(TZ).year
    out, failures = [], []
    for team in TEAMS:
        games, any_ok = [], False
        for league in team["leagues"]:
            url = f'{ESPN}/{team["sport"]}/{league}/teams/{team["id"]}/schedule'
            if team["seasoned"]:
                url += f"?season={season}"
            try:
                data = json.loads(fetch(url))
                any_ok = True
            except Exception as exc:  # noqa: BLE001
                failures.append({"team": team["name"], "league": league,
                                 "reason": short_reason(exc)})
                continue
            for ev in data.get("events", []):
                raw = (ev.get("date") or "")[:19]
                try:
                    when = datetime.strptime(raw, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc) \
                        if len(raw) == 16 else datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                if since <= when <= datetime.now(timezone.utc):
                    rec = game_record(ev, team["name"])
                    rec["league"] = league
                    if rec["completed"]:
                        rec["summary_endpoint"] = (
                            f'{ESPN}/{team["sport"]}/{league}/summary?event={rec["event_id"]}')
                    games.append(rec)

        out.append({"team": team["name"],
                    "status": "ok" if any_ok else "unavailable",
                    "games": games,
                    "note": None if games else "no game in window"})

    return {"status": "ok", "since": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "teams": out, "failures": failures}


# --------------------------------------------------------------------------
# portfolio


def get_portfolio(holdings, api_key):
    if not holdings:
        return {"status": "unavailable", "reason": "no holdings configured"}
    if not api_key:
        return {"status": "unavailable", "reason": "no market data API key set"}
    return {"status": "unavailable", "reason": "price lookup not yet implemented"}


# --------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="DigestConfig.md")
    ap.add_argument("--state", default="last_run.json")
    args = ap.parse_args()

    try:
        cfg = parse_config(args.config)
    except Exception as exc:  # noqa: BLE001 - without config there is nothing to collect
        json.dump({"error": f"could not read {args.config}: {short_reason(exc)}"}, sys.stdout)
        return 1

    since = window_start(load_state(args.state))
    now = datetime.now(timezone.utc)

    out = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "local_date": datetime.now(TZ).strftime("%A, %B %-d, %Y"),
        "window_start": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "weather": guard(get_weather),
        "calendar": guard(get_calendars, cfg["calendars"]),
        "newsletters": guard(get_newsletters, cfg["feeds"], since),
        "sports": guard(get_sports, since),
        "portfolio": guard(get_portfolio, cfg["holdings"], None),
        "todos": {"status": "unavailable", "reason": "no iCloud app-specific password set"},
        "whoop": {"status": "unavailable", "reason": "no WHOOP bridge configured"},
    }
    json.dump(out, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
