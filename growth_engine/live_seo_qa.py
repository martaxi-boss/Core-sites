"""One-off, read-only *live HTTP* SEO verification for the Low Cost Europa pilot.

This checks what a public HTTP client can observe. It is NOT a Google
Search Console URL Inspection call and does NOT prove that URLs are indexed.
Only the 23 public URLs already declared in the canonical sitemap are fetched.
Robots-denied/private URLs are evaluated from robots.txt, never requested.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import time
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError
from urllib.robotparser import RobotFileParser
from urllib.request import Request

import seo_growth_core as core

BASE = "https://www.lowcost-europa.eu"
EXPECTED_EXCLUSIONS = (
    "/admin/", "/painel/", "/ops/", "/health/", "/i18n/",
    "/go/", "/contactar/", "/aliexpress/", "/pesquisar/",
)
SIMULATED_GOOGLEBOT = "Googlebot/2.1 (+http://www.google.com/bot.html)"
GOOGLEBOT_SAMPLES = ("/pt/", "/pt/products/hifu/", "/es/products/hifu/")


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.html_lang = ""
        self.viewport = False
        self.robots_meta = []
        self.canonicals = []
        self.alternates = []
        self.ld_blocks = []
        self._ld = False
        self._fragments = []

    def handle_starttag(self, tag, attrs):
        d = {key.lower(): (val or "") for key, val in attrs}
        if tag == "html":
            self.html_lang = d.get("lang", "").lower()
        if tag == "meta" and d.get("name", "").lower() == "viewport":
            self.viewport = "width=device-width" in d.get("content", "").lower()
        if tag == "meta" and d.get("name", "").lower() in ("robots", "googlebot"):
            self.robots_meta.append(d.get("content", ""))
        if tag == "link":
            rel = d.get("rel", "").lower().split()
            if "canonical" in rel:
                self.canonicals.append(d.get("href", ""))
            if "alternate" in rel and d.get("hreflang"):
                self.alternates.append((d["hreflang"].lower(), d.get("href", "")))
        if tag == "script" and d.get("type", "").lower() == "application/ld+json":
            self._ld = True
            self._fragments = []

    def handle_data(self, data):
        if self._ld:
            self._fragments.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._ld:
            self.ld_blocks.append("".join(self._fragments))
            self._ld = False
            self._fragments = []


def seo_root(path: str) -> str | None:
    if path in ("/", "/pt/", "/es/"):
        return "/"
    for prefix in ("/pt", "/es"):
        if path.startswith(prefix + "/products/") and path.endswith("/"):
            return path[len(prefix):]
    if path.startswith("/products/") and path.endswith("/"):
        return path
    return None


def expected_hreflang(url: str) -> dict[str, str]:
    path = urlsplit(url).path
    root = seo_root(path)
    if root is None:
        return {}
    return {
        "pt-pt": BASE + ("/pt/" if root == "/" else "/pt" + root),
        "es-es": BASE + ("/es/" if root == "/" else "/es" + root),
        "x-default": BASE + root,
    }


def googlebot_rule_for_this_site(robots_text: str, path: str) -> bool:
    """Apply Google's longest-matching path rule to this site's simple robots file.

    Fail closed on patterns or multiple user-agent groups rather than guessing.
    Python urllib.robotparser returns the *first* path match, unlike Google.
    """
    rules = []
    agents = []
    for line in robots_text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.casefold()
        if key == "user-agent":
            agents.append(value.casefold())
        if key in ("allow", "disallow"):
            if "*" in value or "$" in value:
                raise ValueError("Unexpected robots wildcard; requires a full RFC-compliant evaluator")
            if value:
                rules.append((key, value))
    if agents != ["*"]:
        raise ValueError("Unexpected robots user-agent groups; cannot infer Googlebot policy")
    matches = [(len(value), 1 if key == "allow" else 0)
               for key, value in rules if path.startswith(value)]
    if not matches:
        return True
    length, is_allow = max(matches)
    return bool(is_allow)


def evaluate_public_page(url: str, html: bytes, x_robots: str = "") -> dict:
    meta = Metadata()
    meta.feed(html.decode("utf-8", errors="replace"))
    errors = []
    warnings = []
    expected = expected_hreflang(url)

    if len(meta.canonicals) != 1 or meta.canonicals[0] != url:
        errors.append("canonical_missing_or_not_self")
    if not meta.viewport:
        errors.append("missing_mobile_viewport")
    combined_robots = " ".join(meta.robots_meta + [x_robots]).lower()
    if "noindex" in combined_robots or "none" == combined_robots.strip():
        errors.append("noindex_on_public_sitemap_url")
    if expected:
        observed = {}
        for key, href in meta.alternates:
            if key in observed:
                errors.append("duplicate_hreflang_" + key)
            observed[key] = href
        for key, href in expected.items():
            if observed.get(key) != href:
                errors.append("hreflang_" + key + "_wrong_or_missing")
        for key in observed:
            if key not in expected:
                warnings.append("unexpected_hreflang_" + key)
    else:
        if meta.alternates:
            warnings.append("unexpected_hreflang_on_institutional_page")

    path = urlsplit(url).path
    expected_locale = "es" if path.startswith("/es/") else "pt"
    if not meta.html_lang.startswith(expected_locale):
        errors.append("document_language_inconsistent_with_locale")
    if not meta.ld_blocks:
        warnings.append("no_jsonld_on_page")
    for raw in meta.ld_blocks:
        try:
            json.loads(raw)
        except json.JSONDecodeError:
            errors.append("invalid_jsonld_syntax")

    return {
        "url": url, "language": meta.html_lang,
        "canonical": meta.canonicals[0] if meta.canonicals else None,
        "hreflang": dict(meta.alternates), "jsonld_blocks": len(meta.ld_blocks),
        "errors": sorted(set(errors)), "warnings": sorted(set(warnings)),
    }


def googlebot_sample(path: str) -> dict:
    """HTTP UA comparison only. Does not identify as verified Google IP."""
    url = BASE + path
    req = Request(url, headers={
        "User-Agent": SIMULATED_GOOGLEBOT,
        "Accept": "text/html",
    })
    try:
        with core.OPENER.open(req, timeout=core.TIMEOUT) as resp:
            raw = resp.read(core.MAX_BYTES + 1)
            if len(raw) > core.MAX_BYTES:
                raise ValueError("excessive response")
            data = evaluate_public_page(url, raw, ", ".join(resp.headers.get_all("X-Robots-Tag", [])))
            return {
                "path": path, "status": resp.status, "final_url": resp.geturl(),
                "errors": data["errors"],
            }
    except (HTTPError, URLError, TimeoutError, ValueError) as ex:
        return {"path": path, "status": ex.code if isinstance(ex, HTTPError) else None,
                "errors": [type(ex).__name__]}


def perform(site: dict, pause: float = 0.20) -> dict:
    if site.get("id") != "lowcost-europa" or site.get("home") != BASE:
        raise ValueError("Not the authorized Low Cost pilot configuration")
    host = core.origin_host(BASE)
    sitemap = core.list_sitemap(site["sitemap"], host)
    if len(sitemap) > 30:
        raise ValueError("Pilot page count exceeds explicit 30-URL safety cap")
    status, final, raw, _, _ = core.get(BASE + "/robots.txt")
    if status != 200 or final != BASE + "/robots.txt":
        raise ValueError("Unexpected public robots.txt response")
    robots_text = raw.decode("utf-8", errors="replace")
    # Our site has only the simple global '*' group. Prefer Google's longest-rule
    # precedence; Python's RobotFileParser incorrectly treats Allow:/ as first-match.
    googlebot_rule_for_this_site(robots_text, "/")

    public = []
    errors = []
    warnings = []
    for url in sitemap:
        if not googlebot_rule_for_this_site(robots_text, urlsplit(url).path):
            errors.append({"url": url, "problem": "public_sitemap_url_robots_disallow"})
            continue
        try:
            status, final_url, body, content_type, x_robots = core.get(url)
            if status != 200 or final_url != url or "html" not in content_type.lower():
                errors.append({"url": url, "problem": "unexpected_http_status_redirect_or_type",
                               "http": status, "final_url": final_url})
                continue
            page = evaluate_public_page(url, body, x_robots)
            public.append(page)
            for problem in page["errors"]:
                errors.append({"url": url, "problem": problem})
            for problem in page["warnings"]:
                warnings.append({"url": url, "problem": problem})
        except (HTTPError, URLError, TimeoutError, ValueError) as ex:
            errors.append({"url": url, "problem": type(ex).__name__})
        if pause:
            time.sleep(pause)

    private = []
    for path in EXPECTED_EXCLUSIONS:
        allowed = googlebot_rule_for_this_site(robots_text, path + "seo-read-only-nonexistent")
        private.append({"path": path, "googlebot_disallowed": not allowed})
        if allowed:
            errors.append({"url": BASE + path, "problem": "intended_private_area_not_blocked_in_robots"})

    googlebot = []
    for path in GOOGLEBOT_SAMPLES:
        if not googlebot_rule_for_this_site(robots_text, path):
            continue
        result = googlebot_sample(path)
        googlebot.append(result)
        if result.get("status") != 200 or result.get("errors"):
            errors.append({"url": BASE + path, "problem": "googlebot_user_agent_public_sample_difference",
                           "details": result})
        if pause:
            time.sleep(pause)

    if len(public) != len(sitemap):
        errors.append({"url": BASE + "/sitemap.xml", "problem": "incomplete_public_page_audit"})
    return {
        "site": "lowcost-europa", "date_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not errors else "fail",
        "sitemap_urls": len(sitemap), "public_pages_fetched": len(public),
        "public": public, "private_robots": private, "simulated_googlebot": googlebot,
        "errors": errors, "warnings": warnings,
        "limits": (
            "Public HTTP checks only. Googlebot User-Agent is simulated on runner IP; "
            "NOT a real Googlebot or Google Search Console inspection. "
            "Private URLs were NOT fetched. No ranking, index coverage, conversion or buyer data measured."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sites = json.loads(Path(args.config).read_text(encoding="utf-8")).get("sites", [])
    if len(sites) != 1:
        raise SystemExit("Pilot must contain only Low Cost Europa")
    result = perform(sites[0])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "lowcost-europa.live-seo.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    lines = [f"# Live SEO validation: {result['status'].upper()}",
             f"UTC: {result['date_utc']}", "",
             f"Pages: {result['public_pages_fetched']} / {result['sitemap_urls']}",
             f"Errors: {len(result['errors'])}; warnings: {len(result['warnings'])}",
             "", "## Errors", ""]
    lines.extend(f"- {e['url']} — {e['problem']}" for e in result["errors"])
    if not result["errors"]:
        lines.append("- None detected in these live HTTP checks.")
    lines.extend(["", "## Googlebot-User-Agent simulated HTTP sample", ""])
    lines.extend(f"- {x['path']}: HTTP {x.get('status')}, errors={x.get('errors')}" for x in result["simulated_googlebot"])
    lines.extend(["", "## Guardrails", "", result["limits"], ""])
    (out / "lowcost-europa.live-seo.md").write_text("\n".join(lines), encoding="utf-8")
    print("LOWCOST_LIVE_QA=" + result["status"].upper() +
          " PAGES=" + str(result["public_pages_fetched"]) +
          " ERRORS=" + str(len(result["errors"])) +
          " WARNINGS=" + str(len(result["warnings"])) +
          " GOOGLEBOT_SAMPLES=" + str(len(result["simulated_googlebot"])))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
