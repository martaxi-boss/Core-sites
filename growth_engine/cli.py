"""CLI that converts public SEO audit observations into review-only growth work."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from .gsc import load_csv
from .planner import markdown, plan
from .privacy import redact_report


def main() -> int:
    p = argparse.ArgumentParser(description="Build a restrained SEO growth backlog from observed page reports")
    p.add_argument("--config", required=True, help="Public sites.json registry")
    p.add_argument("--audit-dir", required=True, help="Directory with v1 per-site audit JSON")
    p.add_argument("--out", required=True, help="Directory for growth JSON and Markdown reports")
    p.add_argument("--gsc-dir", default=None, help="Optional LOCAL private joint query+page CSVs, named SITE.csv")
    args = p.parse_args()
    if args.gsc_dir and os.getenv("GITHUB_ACTIONS", "").lower() == "true":
        p.error("Private GSC exports must never be read in public GitHub Actions artifacts")
    sites = json.loads(Path(args.config).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    status = 0
    for site in sites["sites"]:
        audit_path = Path(args.audit_dir) / (site["id"] + ".json")
        if not audit_path.exists():
            print(f"ERROR {site['id']}: source audit missing")
            status = 1
            continue
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        rows = None
        diagnostics = None
        if args.gsc_dir:
            path = Path(args.gsc_dir) / (site["id"] + ".csv")
            if path.exists():
                rows, diagnostics = load_csv(path, urlsplit(site["home"]).hostname or "",
                                             country_filter=site.get("gsc_country"))
        growth = plan(audit, site, rows, diagnostics)
        (out / (site["id"] + ".growth.json")).write_text(
            json.dumps(redact_report(growth), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out / (site["id"] + ".growth.md")).write_text(markdown(growth, public=True), encoding="utf-8")
        if rows is not None:
            print(f"{site['id']}: GSC evaluated in memory; exported JSON and Markdown are redacted")
        else:
            print(f"{site['id']}: {len(growth['priority_queue'])} proposals, "
                  f"{len(growth['briefs'])} draft briefs (GSC not connected)")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
