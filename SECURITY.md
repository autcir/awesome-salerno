# Security Policy

## Scope

Awesome Salerno is a curated list of links plus the scripts that generate and
verify it. There is no user account, no database of personal data and nothing
that runs on your machine beyond a static site.

So the security surface here is not a server — it is the **content**:

- **Malicious, hijacked or defaced links** — a POI, event or external resource
  URL that now serves malware, phishing pages or unexpected adult/scam
  content.
- **Typosquatted or look-alike domains** — entries that imitate an official
  site (`comune-di-salerno.it` instead of `comune.salerno.it`), so that a
  visitor lands somewhere they did not mean to go.
- **License and attribution problems in the listed resources** — content,
  images or data redistributed under a license that does not allow it, or
  without the attribution the license requires. This is the license surface
  of a curated list, and it is the part contributors are most likely to get
  wrong by accident.
- **Repository integrity** — anything in `scripts/`, `api/` or the GitHub
  Actions workflows that executes or fetches something the file does not
  declare. The auto-refresh, link-check and digest jobs run unattended on a
  schedule, so a compromised dependency or feed would be able to act here.

## Supported versions

Only the `main` branch and the current GitHub Pages deployment are maintained.
Past versions of the generated dataset in `data/` are not patched — problems
are fixed forward in the current files, and the link-check workflow rewrites
them on the next run.

## Reporting a vulnerability

**Please do not open a public issue for these.**

Report privately through [GitHub Security Advisories](../../security/advisories/new)
(the *Security* tab → *Report a vulnerability*) or by email to
`security@studiocentos.com`.

Include the URL(s) involved and what you observed. If the report is about a
listed resource, a link to the correct or official domain makes the repair
much faster. Reports are kept confidential until a fix is in place.

There is no response SLA: this list is maintained in spare time, so please
allow a few days before following up.

A link that is merely *broken* is a bug, not a vulnerability — the
[broken-link issue template](../../issues/new/choose) is the faster route for
those and is always welcome.
