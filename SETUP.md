# SETUP — attaching the repository to the Routine

The digest publishes by pushing to `claude/clever-feynman-w6afpi`, which GitHub
Pages serves. Everything else runs unattended; **this is the one step that needs
a human**, because a Routine's repository list can only be set in the web UI.

## The problem this solves

A Routine is a saved configuration of a prompt, **one or more repositories**,
and a set of connectors. Each repository is cloned at the start of every run.

The Routine here was originally created through the `create_trigger` MCP tool,
which has no repositories field. So every firing spawned a session with nothing
cloned and no scoped git credential, and died immediately:

- `no repo checkout found`
- `not in session's authorized set`

Roughly ten scheduled runs published nothing, silently, over a week before this
was diagnosed. Notifications are now on, so a failure reports itself — but
publishing stays blocked until the repository is attached.

Note for anyone tempted by a token workaround: don't. Cloud environments have
no secrets store, the docs explicitly advise against putting credentials in
environment variables, and a token wouldn't fix this anyway — the session needs
the repo *attached*, not just reachable. Pushes to `claude/`-prefixed branches
are always accepted once it is.

---

## Fix: attach the repository

1. Go to <https://claude.ai/code/routines>
2. Click **Trujillo Times morning digest**
3. Click the **pencil icon** to open **Edit routine**
4. Under **Select repositories**, add **`trujillo-matt/TrujTimes`**
5. **Save**

---

## Also check: network access

The **Default** environment uses **Trusted** network access, which allows only a
default allowlist of package registries, cloud provider APIs, container
registries, and common development domains. The digest's sources are none of
those. Requests to hosts outside the list fail with `403` and
`x-deny-reason: host_not_allowed`.

In **Edit routine**, select the cloud icon showing **Default**, hover the
environment, click the **settings icon**, and in **Update cloud environment**
set **Network access** to **Custom**. Tick **Also include default list of
common package managers**, then add:

```
api.weather.gov
p116-caldav.icloud.com
outlook.office365.com
kill-the-newsletter.com
artofmanliness.com
www.palladiummag.com
theverge.com
www.bytedrum.com
blessthisstuff.com
coolmaterial.com
feeds.feedburner.com
site.api.espn.com
query1.finance.yahoo.com
```

Choose **Full** instead if you'd rather not maintain the list. Web search needs
no entries — that traffic routes through Anthropic's servers, not the session's
network.

Keep this list in step with the feeds in `DigestConfig.md`: adding a newsletter
on a new host means adding its domain here too, or that one feed quietly starts
reporting as unavailable.

---

## Verifying

Open the routine and click **Run now** rather than waiting for 5:30 AM.

Success: a commit on `claude/clever-feynman-w6afpi` within a few minutes, a new
dated page under `docs/0f3f5a3a42464db1dea0cd43/`, both feeds rebuilt, and the
deployed `rss.xml` still passing the KOReader gate.

**A green status in the run list is not proof of success.** It means the session
started and exited without an infrastructure error, not that the digest
published. Confirm by checking for the new dated entry in the feed.

To see what a run actually did, open <https://claude.ai/code/routines>, click
the routine, then click any run to open it as a full session and read the
transcript. Watch for `403` / `host_not_allowed`, which is the signature of the
network allowlist above.
