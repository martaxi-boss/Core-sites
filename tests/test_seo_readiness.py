import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from growth_engine import seo_readiness as readiness


HOME = "https://www.lowcost-europa.eu"
PAGES = [HOME + "/", HOME + "/pt/", HOME + "/es/"]
SITE = {"id": "lowcost-europa", "home": HOME, "sitemap": HOME + "/sitemap.xml"}


def xml(pages):
    locs = "".join("<url><loc>" + url + "</loc></url>" for url in pages)
    return ('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + locs + "</urlset>").encode()


def crawl(pages=None, partial=False):
    items = pages if pages is not None else PAGES
    return {
        "site": "lowcost-europa", "sitemap_urls": len(items),
        "pages_scanned": len(items), "partial_scan": partial,
        "findings": [], "page_signals": [{"url": u} for u in items],
    }


def mock_probe(modified_txt=None, modified_robots=None):
    values = {
        "xml": (xml(PAGES), "application/xml"),
        "txt": (("\n".join(PAGES) + "\n").encode(), "text/plain"),
        "robots": ((
            "User-agent: *\nAllow: /\n\n"
            "Sitemap: " + HOME + "/sitemap.xml\n"
            "Sitemap: " + HOME + "/sitemap.txt\n"
        ).encode(), "text/plain"),
    }
    if modified_txt is not None:
        values["txt"] = (modified_txt.encode(), "text/plain")
    if modified_robots is not None:
        values["robots"] = (modified_robots.encode(), "text/plain")

    def callback(url, host):
        if not url.startswith(HOME + "/") or host != "www.lowcost-europa.eu":
            raise AssertionError("Unexpected URL/host")
        if url.endswith("sitemap.xml"):
            return values["xml"]
        if url.endswith("sitemap.txt"):
            return values["txt"]
        if url.endswith("robots.txt"):
            return values["robots"]
        raise AssertionError("Unexpected URL")
    return callback


class LowcostReadinessTests(unittest.TestCase):
    def test_xml_txt_parity_and_googlebot_pass(self):
        with patch.object(readiness, "public_probe", side_effect=mock_probe()):
            report = readiness.inspect(SITE, crawl())
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["checks"]["xml_txt_parity"]["xml_urls"], 3)
        self.assertTrue(report["checks"]["xml_txt_parity"]["passed"])
        self.assertEqual(report["checks"]["robots"]["googlebot_denied"], 0)
        self.assertEqual(report["search_consoles"]["google"], "not_authenticated_in_this_audit")

    def test_txt_different_from_xml_is_a_real_failure(self):
        with patch.object(readiness, "public_probe",
                          side_effect=mock_probe(modified_txt="\n".join(PAGES[:2]))):
            report = readiness.inspect(SITE, crawl())
        self.assertEqual(report["status"], "fail")
        self.assertFalse(report["checks"]["xml_txt_parity"]["passed"])
        self.assertTrue(any("mismatch" in e.lower() for e in report["errors"]))

    def test_googlebot_disallowed_is_a_real_failure(self):
        robots = ("User-agent: Googlebot\nDisallow: /\n"
                  "User-agent: *\nAllow: /\n"
                  "Sitemap: " + HOME + "/sitemap.xml\n"
                  "Sitemap: " + HOME + "/sitemap.txt\n")
        with patch.object(readiness, "public_probe", side_effect=mock_probe(modified_robots=robots)):
            report = readiness.inspect(SITE, crawl())
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["checks"]["robots"]["googlebot_denied"], 3)

    def test_absent_txt_declaration_is_failure(self):
        robots = ("User-agent: *\nAllow: /\n"
                  "Sitemap: " + HOME + "/sitemap.xml\n")
        with patch.object(readiness, "public_probe", side_effect=mock_probe(modified_robots=robots)):
            report = readiness.inspect(SITE, crawl())
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("does not advertise both" in e for e in report["errors"]))

    def test_incomplete_html_crawl_is_failure(self):
        with patch.object(readiness, "public_probe", side_effect=mock_probe()):
            report = readiness.inspect(SITE, crawl(partial=True))
        self.assertEqual(report["status"], "fail")
        self.assertIn("HTML crawl is partial or incomplete", report["errors"])

    def test_missing_endpoint_never_silently_passes(self):
        def broken(url, host):
            if url.endswith("sitemap.txt"):
                raise TimeoutError("fail")
            return mock_probe()(url, host)
        with patch.object(readiness, "public_probe", side_effect=broken):
            report = readiness.inspect(SITE, crawl())
        self.assertEqual(report["status"], "fail")
        self.assertIsNone(report["checks"]["txt"]["http"])

    def test_refuses_other_sites_in_pilot(self):
        with self.assertRaisesRegex(ValueError, "Low Cost"):
            readiness.inspect({**SITE, "id": "sevelora"}, crawl())


if __name__ == "__main__":
    unittest.main()
