#!/usr/bin/env python3
"""
dorker.py — Passive recon tool for bug bounty programs.

Queries a search API (Google Custom Search JSON API or Bing Web Search API)
for files/paths on a target domain, plus the Wayback Machine CDX API and
crt.sh for additional passive coverage. Results are deduplicated, optionally
checked for liveness, and written to a single CSV/JSON report.

IMPORTANT: Only point this at targets that are explicitly in scope for a
program you are authorized to test. Respect the program's rules on rate
limits and automated scanning.

Setup
-----
Google Custom Search API (recommended):
    1. Create a Programmable Search Engine: https://programmablesearchengine.google.com/
       - Set it to search the entire web.
    2. Get an API key: https://console.cloud.google.com/apis/credentials
       - Enable the "Custom Search API".
    3. Export credentials:
         export GOOGLE_CSE_ID="your_search_engine_id"
         export GOOGLE_CSE_KEY="your_api_key"

Bing Web Search API (alternative):
    export BING_API_KEY="your_api_key"

If neither is configured, the script still runs using Wayback + crt.sh only.

Usage
-----
    python dorker.py example.com --filetypes pdf,docx,xlsx,env,log \
        --out-dir ./results --check-live --max-pages 3

    python dorker.py example.com --dorks dorks.txt --scope scope.txt

    # dorks.txt example (one template per line, {domain} is substituted):
    #   site:{domain} ext:env | ext:log
    #   site:{domain} intitle:"index of"
    #   site:{domain} inurl:admin

    # scope.txt example (one allowed domain/suffix per line):
    #   example.com
    #   api.example.com
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

DEFAULT_FILETYPES = [
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "xml",
    "json", "sql", "zip", "rar", "7z", "tar", "gz", "log", "bak", "conf",
    "ini", "env", "yaml", "yml",
]

USER_AGENT = "dorker-recon-tool/1.0 (+authorized bug bounty recon)"


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class Finding:
    url: str
    source: str          # "google", "bing", "wayback", "crtsh"
    query: str = ""
    filetype: str = ""
    status_code: int | None = None
    content_type: str = ""
    content_length: int | None = None
    checked_at: str = ""


# --------------------------------------------------------------------------
# Scope control
# --------------------------------------------------------------------------

def load_scope(scope_file: str | None, fallback_domain: str) -> list[str]:
    """Return a list of allowed domain suffixes. Defaults to the target domain."""
    if not scope_file:
        return [fallback_domain.lower()]
    with open(scope_file, "r", encoding="utf-8") as f:
        domains = [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]
    return domains or [fallback_domain.lower()]


def in_scope(url: str, allowed_domains: list[str]) -> bool:
    try:
        host = urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return False
    if not host:
        return False
    return any(host == d or host.endswith("." + d) for d in allowed_domains)


# --------------------------------------------------------------------------
# Rate-limited session
# --------------------------------------------------------------------------

class ThrottledSession:
    def __init__(self, min_delay: float = 1.5, max_delay: float = 3.5):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.min_delay = min_delay
        self.max_delay = max_delay

    def get(self, url: str, **kwargs) -> requests.Response | None:
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
        backoff = 2.0
        for attempt in range(4):
            try:
                resp = self.session.get(url, timeout=15, **kwargs)
            except requests.exceptions.RequestException as e:
                print(f"  [warn] request error: {e}")
                return None
            if resp.status_code == 429 or resp.status_code >= 500:
                wait = backoff * (attempt + 1)
                print(f"  [warn] got {resp.status_code}, backing off {wait:.1f}s")
                time.sleep(wait)
                continue
            return resp
        print("  [warn] giving up after repeated errors")
        return None


# --------------------------------------------------------------------------
# Search sources
# --------------------------------------------------------------------------

def google_cse_search(session: ThrottledSession, query: str, max_pages: int) -> list[str]:
    """Google Programmable Search Engine (Custom Search JSON API)."""
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    cse_key = os.environ.get("GOOGLE_CSE_KEY")
    if not (cse_id and cse_key):
        return []

    links = []
    for page in range(max_pages):
        start = page * 10 + 1
        resp = session.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": cse_key, "cx": cse_id, "q": query, "start": start},
        )
        if resp is None or resp.status_code != 200:
            if resp is not None:
                print(f"  [warn] Google CSE returned {resp.status_code}: {resp.text[:200]}")
            break
        data = resp.json()
        items = data.get("items", [])
        if not items:
            break
        for item in items:
            link = item.get("link")
            if link:
                links.append(link)
        if "nextPage" not in data.get("queries", {}):
            break
    return links


def bing_search(session: ThrottledSession, query: str, max_pages: int) -> list[str]:
    api_key = os.environ.get("BING_API_KEY")
    if not api_key:
        return []

    links = []
    for page in range(max_pages):
        offset = page * 50
        resp = session.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers={"Ocp-Apim-Subscription-Key": api_key},
            params={"q": query, "count": 50, "offset": offset},
        )
        if resp is None or resp.status_code != 200:
            if resp is not None:
                print(f"  [warn] Bing returned {resp.status_code}: {resp.text[:200]}")
            break
        data = resp.json()
        results = data.get("webPages", {}).get("value", [])
        if not results:
            break
        for item in results:
            url = item.get("url")
            if url:
                links.append(url)
    return links


def wayback_search(session: ThrottledSession, domain: str) -> list[str]:
    """Wayback Machine CDX API — archived URLs under the domain, no API key needed."""
    resp = session.get(
        "https://web.archive.org/cdx/search/cdx",
        params={
            "url": f"*.{domain}/*",
            "output": "json",
            "fl": "original",
            "collapse": "urlkey",
            "limit": "20000",
        },
    )
    if resp is None or resp.status_code != 200:
        return []
    try:
        rows = resp.json()
    except ValueError:
        return []
    if not rows or len(rows) < 2:
        return []
    return [row[0] for row in rows[1:]]  # first row is the header


def crtsh_subdomains(session: ThrottledSession, domain: str) -> list[str]:
    """crt.sh certificate transparency lookup — returns hostnames (not full URLs)."""
    resp = session.get(f"https://crt.sh/?q=%.{domain}&output=json")
    if resp is None or resp.status_code != 200:
        return []
    try:
        rows = resp.json()
    except ValueError:
        return []
    names = set()
    for row in rows:
        for n in row.get("name_value", "").split("\n"):
            n = n.strip().lower().lstrip("*.")
            if n:
                names.add(n)
    return [f"https://{n}" for n in names]


# --------------------------------------------------------------------------
# Liveness check
# --------------------------------------------------------------------------

def check_liveness(session: ThrottledSession, finding: Finding) -> None:
    resp = session.get(finding.url, allow_redirects=True)
    finding.checked_at = datetime.now(timezone.utc).isoformat()
    if resp is None:
        finding.status_code = None
        return
    finding.status_code = resp.status_code
    finding.content_type = resp.headers.get("Content-Type", "")
    cl = resp.headers.get("Content-Length")
    finding.content_length = int(cl) if cl and cl.isdigit() else None


# --------------------------------------------------------------------------
# Dork handling
# --------------------------------------------------------------------------

def default_dorks(domain: str, filetypes: list[str]) -> list[tuple[str, str]]:
    """Returns list of (query, filetype_label) tuples."""
    return [(f"site:{domain} filetype:{ft}", ft) for ft in filetypes]


def load_dork_templates(path: str, domain: str) -> list[tuple[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        templates = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return [(t.format(domain=domain), "") for t in templates]


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Passive recon: search-engine dorking + Wayback + crt.sh for an authorized target."
    )
    parser.add_argument("domain", help="Target domain, e.g. example.com (no http/https)")
    parser.add_argument("--filetypes", default=",".join(DEFAULT_FILETYPES),
                         help="Comma-separated filetypes to dork for (ignored if --dorks is given)")
    parser.add_argument("--dorks", help="Path to a file of custom dork templates (use {domain} placeholder)")
    parser.add_argument("--scope", help="Path to a file listing in-scope domains (one per line)")
    parser.add_argument("--out-dir", default="./dorker_results", help="Output directory")
    parser.add_argument("--max-pages", type=int, default=2, help="Max result pages per dork query (API only)")
    parser.add_argument("--check-live", action="store_true", help="HEAD/GET-check each found URL for status/size")
    parser.add_argument("--skip-wayback", action="store_true", help="Skip Wayback Machine lookup")
    parser.add_argument("--skip-crtsh", action="store_true", help="Skip crt.sh subdomain lookup")
    parser.add_argument("--min-delay", type=float, default=1.5, help="Minimum seconds between requests")
    parser.add_argument("--max-delay", type=float, default=3.5, help="Maximum seconds between requests")
    args = parser.parse_args()

    domain = args.domain.strip().lower()
    domain = re.sub(r"^https?://", "", domain).strip("/")

    allowed_domains = load_scope(args.scope, domain)
    print(f"Scope: {allowed_domains}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    session = ThrottledSession(args.min_delay, args.max_delay)

    have_google = bool(os.environ.get("GOOGLE_CSE_ID") and os.environ.get("GOOGLE_CSE_KEY"))
    have_bing = bool(os.environ.get("BING_API_KEY"))
    if not (have_google or have_bing):
        print("[info] No GOOGLE_CSE_ID/GOOGLE_CSE_KEY or BING_API_KEY set — "
              "skipping search-engine dorking, using Wayback + crt.sh only.")

    findings: dict[str, Finding] = {}  # url -> Finding, deduped

    def record(url: str, source: str, query: str = "", filetype: str = ""):
        if not in_scope(url, allowed_domains):
            return
        if url not in findings:
            findings[url] = Finding(url=url, source=source, query=query, filetype=filetype)

    # --- Dork-based search ---
    if have_google or have_bing:
        if args.dorks:
            dorks = load_dork_templates(args.dorks, domain)
        else:
            filetypes = [ft.strip() for ft in args.filetypes.split(",") if ft.strip()]
            dorks = default_dorks(domain, filetypes)

        for query, ft in dorks:
            print(f"Querying: {query}")
            if have_google:
                for url in google_cse_search(session, query, args.max_pages):
                    record(url, "google", query, ft)
            if have_bing:
                for url in bing_search(session, query, args.max_pages):
                    record(url, "bing", query, ft)

    # --- Wayback Machine ---
    if not args.skip_wayback:
        print(f"Querying Wayback Machine CDX for *.{domain}/* ...")
        for url in wayback_search(session, domain):
            record(url, "wayback")

    # --- crt.sh ---
    if not args.skip_crtsh:
        print(f"Querying crt.sh for *.{domain} ...")
        for url in crtsh_subdomains(session, domain):
            record(url, "crtsh")

    print(f"\nTotal unique in-scope findings: {len(findings)}")

    # --- Liveness check ---
    if args.check_live and findings:
        print("Checking liveness of findings (this can take a while)...")
        for i, finding in enumerate(findings.values(), 1):
            check_liveness(session, finding)
            if i % 25 == 0:
                print(f"  checked {i}/{len(findings)}")

    # --- Write combined report ---
    csv_path = out_dir / f"{domain}_findings.csv"
    json_path = out_dir / f"{domain}_findings.json"

    rows = sorted(findings.values(), key=lambda f: f.url)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "source", "query", "filetype", "status_code",
                          "content_type", "content_length", "checked_at"])
        for r in rows:
            writer.writerow([r.url, r.source, r.query, r.filetype, r.status_code,
                              r.content_type, r.content_length, r.checked_at])

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([r.__dict__ for r in rows], f, indent=2)

    print(f"\nSaved {len(rows)} findings to:\n  {csv_path}\n  {json_path}")


if __name__ == "__main__":
    main()
