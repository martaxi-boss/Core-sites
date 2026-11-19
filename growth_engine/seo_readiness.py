"""Read-only public sitemap and Googlebot readiness checks for Core-sites pilots.

This is not a Google Search Console/Bing API integration. Console account state,
index coverage, impressions and positions cannot be inferred from HTTP responses.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.robotparser import RobotFileParser

import seo_growth_core as core


def public_probe(url: str, host: str) -> tuple[bytes, str]:
    """Use core's bounded HTTPS/same-host client, including redirect protections."""
    status, final_url, body, content_type, x_robots = core.get(url)
    if status != 200:
        raise ValueError(f"HTTP {status} at {url}")
    if core.safe_url(final_url, host) != core.safe_url(url, host):
        raise ValueError(f"Canonical public endpoint redirected: {url}")
    return body, content_type


def inspect(site: dict, crawl: dict) -> dict:
    """Compare XML/TXT/robots and the recorded HTML crawl; never mutate the website."""
    home = site["home"].rstrip("/")
    host = core.origin_host(home)
    xml_url = site["sitemap"]
    txt_url = home + "/sitemap.txt"
    robots_url = home + "/robots.txt"
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, dict] = {}
    xml_urls: list[str] = []
    txt_urls: list[str] = []
    robots_text = ""

    if site.get("id") != "lowcost-europa":
        raise ValueError("This bounded pilot is authorized only for Low Cost Europa")
    if (core.safe_url(xml_url, host) != xml_url or
            core.safe_url(txt_url, host) != txt_url):
        raise ValueError("Pilot endpoints must be canonical HTTPS URLs on the same host")

    for kind, url in (("xml", xml_url), ("txt", txt_url), ("robots", robots_url)):
        try:
            data, content_type = public_probe(url, host)
            checks[kind] = {"http": 200, "url": url, "bytes": len(data), "content_type": content_type}
            if kind == "xml":
                xml_kind, raw_urls = core.xml_locs(data)
                if xml_kind != "urlset":
                    errors.append("XML sitemap is not a root urlset; review nested indexes before comparing")
                for raw in raw_urls:
                    candidate = core.safe_url(raw, host)
                    if candidate is None:
                        errors.append("XML sitemap contains an unsafe/out-of-host URL")
                        continue
                    if candidate != raw:
                        errors.append("XML sitemap URL is not normalized as canonical HTTPS")
                    xml_urls.append(candidate)
            elif kind == "txt":
                for raw in data.decode("utf-8-sig", errors="strict").splitlines():
                    raw = raw.strip()
                    if not raw or raw.startswith("#"):
                        continue
                    candidate = core.safe_url(raw, host)
                    if candidate is None:
                        errors.append("TXT sitemap contains an unsafe/out-of-host URL")
                        continue
                    if candidate != raw:
                        errors.append("TXT sitemap URL is not normalized as canonical HTTPS")
                    txt_urls.append(candidate)
            else:
                robots_text = data.decode("utf-8-sig", errors="replace")
        except Exception as exc:
            checks[kind] = {"http": None, "url": url, "error_type": type(exc).__name__}
            errors.append(f"{kind.upper()} public endpoint check failed ({type(exc).__name__})")

    if xml_urls and txt_urls:
        a, b = set(xml_urls), set(txt_urls)
        if len(xml_urls) != len(a):
            errors.append("XML sitemap contains duplicated URLs")
        if len(txt_urls) != len(b):
            errors.append("TXT sitemap contains duplicated URLs")
        if a != b:
            errors.append(f"XML/TXT sitemap mismatch: only_xml={len(a-b)}, only_txt={len(b-a)}")
        checks["xml_txt_parity"] = {
            "passed": a == b and len(xml_urls) == len(a) and len(txt_urls) == len(b),
            "xml_urls": len(xml_urls), "txt_urls": len(txt_urls),
        }
    else:
        errors.append("Cannot establish XML/TXT parity because one sitemap has no valid URLs")
        checks["xml_txt_parity"] = {"passed": False, "xml_urls": len(xml_urls), "txt_urls": len(txt_urls)}

    if robots_text:
        declared = []
        for line in robots_text.splitlines():
            line = line.strip()
            if line.casefold().startswith("sitemap:"):
                declared.append(line.split(":", 1)[1].strip())
        missing_declarations = [url for url in (xml_url, txt_url) if url not in declared]
        if missing_declarations:
            errors.append("robots.txt does not advertise both canonical XML and TXT sitemaps")
        robots = RobotFileParser()
        robots.parse(robots_text.splitlines())
        sample = xml_urls or txt_urls
        denied_google = [url for url in sample if not robots.can_fetch("Googlebot", url)]
        denied_core = [url for url in sample if not robots.can_fetch(core.AGENT, url)]
        if denied_google:
            errors.append(f"robots.txt blocks Googlebot on {len(denied_google)} declared sitemap URLs")
        if denied_core:
            errors.append(f"robots.txt blocks the Core-sites crawler on {len(denied_core)} declared sitemap URLs")
        checks["robots"] = {
            "http": 200, "declares_xml": xml_url in declared, "declares_txt": txt_url in declared,
            "declared_sitemap_urls": len(declared), "googlebot_denied": len(denied_google),
            "core_crawler_denied": len(denied_core),
        }

    if crawl.get("site") != site["id"]:
        errors.append("HTML crawl does not belong to the expected pilot site")
    if crawl.get("partial_scan") is not False:
        errors.append("HTML crawl is partial or incomplete")
    crawled = {row.get("url") for row in crawl.get("page_signals", [])}
    if len(crawled) != crawl.get("pages_scanned") or len(crawled) != len(xml_urls):
        errors.append("HTML crawl coverage differs from the public sitemap")
    if xml_urls and crawled != set(xml_urls):
        errors.append("HTML crawl and XML sitemap URL sets do not match")
    severity = {"critical": 0, "important": 0, "opportunity": 0}
    for finding in crawl.get("findings", []):
        level = finding.get("level")
        if level in severity:
            severity[level] += 1
    if severity["critical"]:
        errors.append(f"HTML audit detected {severity['critical']} critical problems")
    if severity["important"]:
        warnings.append(f"HTML audit detected {severity['important']} issues requiring review")
    checks["html_audit"] = {
        "pages_scanned": crawl.get("pages_scanned"),
        "sitemap_count_reported": crawl.get("sitemap_urls"),
        "partial": crawl.get("partial_scan"),
        "severity": severity,
    }

    warnings.append(
        "No authenticated Search Console or Bing Webmaster API has been queried; "
        "sitemap delivery is not proof of Google/Bing indexing or ranking."
    )
    return {
        "schema": 1,
        "site": site["id"], "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not errors else "fail",
        "checks": checks, "errors": errors, "warnings": warnings,
        "search_consoles": {
            "google": "not_authenticated_in_this_audit",
            "bing": "not_authenticated_in_this_audit",
            "other": "not_authenticated_in_this_audit",
        },
        "disclaimer": "Read-only public HTTP plus saved HTML audit; does not measure indexed URLs, rank, conversions or real visitors.",
    }


def markdown(report: dict) -> str:
    c = report["checks"]
    lines = [
        f"# Readiness SEO — {report['site']}",
        "",
        f"Executado: {report['checked_at_utc']}",
        f"Resultado: **{report['status'].upper()}**",
        "",
        f"- Sitemap XML: {c.get('xml', {}).get('http') or 'erro'}",
        f"- Sitemap TXT: {c.get('txt', {}).get('http') or 'erro'}",
        f"- robots.txt: {c.get('robots', {}).get('http') or 'erro'}",
        f"- XML/TXT: {c.get('xml_txt_parity', {}).get('xml_urls', 0)} / "
        f"{c.get('xml_txt_parity', {}).get('txt_urls', 0)} URLs, "
        f"igualdade={'sim' if c.get('xml_txt_parity', {}).get('passed') else 'não'}",
        f"- HTML: {c.get('html_audit', {}).get('pages_scanned', 0)} páginas",
        "", "## Erros", "",
    ]
    lines.extend(f"- {message}" for message in report["errors"])
    if not report["errors"]:
        lines.append("- Nenhum nesta verificação pública.")
    lines.extend(["", "## Limites e ressalvas", ""])
    lines.extend(f"- {message}" for message in report["warnings"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--audit-dir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if len(config.get("sites", [])) != 1 or config["sites"][0].get("id") != "lowcost-europa":
        raise SystemExit("Pilot is restricted to exactly one authorized Low Cost Europa site")
    site = config["sites"][0]
    crawl = json.loads((Path(args.audit_dir) / "lowcost-europa.json").read_text(encoding="utf-8"))
    report = inspect(site, crawl)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "lowcost-europa.readiness.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "lowcost-europa.readiness.md").write_text(markdown(report), encoding="utf-8")
    checks = report["checks"]
    parity = checks.get("xml_txt_parity", {})
    print(f"LOWCOST_READINESS={report['status'].upper()} "
          f"XML_URLS={parity.get('xml_urls')} TXT_URLS={parity.get('txt_urls')} "
          f"HTML_PAGES={checks.get('html_audit', {}).get('pages_scanned')}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
