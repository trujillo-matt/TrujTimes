#!/usr/bin/env python3
"""Build the Atom and RSS feeds from the dated digest pages.

Source of truth is the set of <YYYY-MM-DD>.html pages in FEED_DIR. Each one
carries its publish time in a <meta name="published"> tag. This script
regenerates both feeds from those pages and prunes anything past RETENTION_DAYS.

Two KOReader constraints are load-bearing here, both verified against
newsdownloader.koplugin/main.lua:
  * A feed is only accepted when the first item has BOTH a title and a link
    (main.lua:575 for RSS, :591 for Atom). A missing link is reported as the
    misleading "Couldn't process RSS".
  * The article body comes from <description> for RSS and <content> for Atom
    (main.lua:761-768).
"""

import html
import json
import os
import re
from datetime import datetime, timedelta, timezone

BASE = "https://trujillo-matt.github.io/TrujTimes/0f3f5a3a42464db1dea0cd43"
FEED_DIR = "docs/0f3f5a3a42464db1dea0cd43"
TITLE = "Trujillo Times Morning Digest"
AUTHOR = "Trujillo Times Digest"
RETENTION_DAYS = 14

DATED_PAGE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.html$")
RFC822 = "%a, %d %b %Y %H:%M:%S +0000"


def load_pages():
    """Return [(date, published_dt, title, body_html)], newest first."""
    out = []
    for name in os.listdir(FEED_DIR):
        m = DATED_PAGE.match(name)
        if not m:
            continue
        raw = open(os.path.join(FEED_DIR, name), encoding="utf-8").read()

        pub = re.search(r'<meta name="published" content="([^"]+)"', raw)
        if not pub:
            raise SystemExit(f"{name} is missing its <meta name='published'> tag")
        published = datetime.strptime(pub.group(1), "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )

        title = re.search(r"<title>(.*?)</title>", raw, re.S)
        body = re.search(r"<body>(.*?)</body>", raw, re.S)
        if not title or not body:
            raise SystemExit(f"{name} is missing a <title> or <body>")

        out.append((m.group(1), published, title.group(1).strip(), body.group(1).strip()))
    return sorted(out, key=lambda r: r[1], reverse=True)


def prune(pages):
    """Drop pages older than the retention window, deleting their files."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    keep, dropped = [], []
    for page in pages:
        if page[1] < cutoff:
            os.remove(os.path.join(FEED_DIR, f"{page[0]}.html"))
            dropped.append(page[0])
        else:
            keep.append(page)
    return keep, dropped


def build_atom(pages, updated):
    entries = []
    for date, published, title, body in pages:
        stamp = published.strftime("%Y-%m-%dT%H:%M:%SZ")
        entries.append(f"""  <entry>
    <title>{html.escape(title)}</title>
    <id>tag:trujillo-matt.github.io,{date}:trujtimes/digest/{date}</id>
    <link rel="alternate" type="text/html" href="{BASE}/{date}.html"/>
    <updated>{stamp}</updated>
    <published>{stamp}</published>
    <content type="html">{html.escape(body)}</content>
  </entry>""")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{html.escape(TITLE)}</title>
  <id>tag:trujillo-matt.github.io,2026:trujtimes-morning-digest</id>
  <link rel="self" type="application/atom+xml" href="{BASE}/feed.xml"/>
  <link rel="alternate" type="text/html" href="{BASE}/"/>
  <updated>{updated}</updated>
  <author><name>{html.escape(AUTHOR)}</name></author>
{chr(10).join(entries)}
</feed>
"""


def build_rss(pages, updated_rfc822):
    items = []
    for date, published, title, body in pages:
        # CDATA keeps the HTML body out of the entity-escaping path entirely.
        safe_body = body.replace("]]>", "]]&gt;")
        items.append(f"""    <item>
      <title>{html.escape(title)}</title>
      <link>{BASE}/{date}.html</link>
      <guid isPermaLink="false">trujtimes-digest-{date}</guid>
      <pubDate>{published.strftime(RFC822)}</pubDate>
      <description><![CDATA[{safe_body}]]></description>
    </item>""")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>{html.escape(TITLE)}</title>
    <link>{BASE}/</link>
    <description>Daily morning digest for the Kindle.</description>
    <language>en-us</language>
    <lastBuildDate>{updated_rfc822}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""


def main():
    pages = load_pages()
    if not pages:
        raise SystemExit(f"no dated digest pages found in {FEED_DIR}")
    pages, dropped = prune(pages)

    newest = pages[0][1]
    open(f"{FEED_DIR}/feed.xml", "w", encoding="utf-8").write(
        build_atom(pages, newest.strftime("%Y-%m-%dT%H:%M:%SZ"))
    )
    open(f"{FEED_DIR}/rss.xml", "w", encoding="utf-8").write(
        build_rss(pages, newest.strftime(RFC822))
    )

    print(json.dumps({"entries": len(pages), "pruned": dropped}, indent=2))


if __name__ == "__main__":
    main()
