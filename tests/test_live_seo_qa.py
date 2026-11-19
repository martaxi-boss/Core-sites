import unittest
from unittest.mock import patch

from growth_engine import live_seo_qa as qa


def page(url, locale="pt-pt", with_jsonld=True):
    alternatives = qa.expected_hreflang(url)
    links = "".join(
        f'<link rel="alternate" hreflang="{language}" href="{href}">'
        for language, href in alternatives.items()
    )
    blocks = '<script type="application/ld+json">{"@type":"WebPage"}</script>' if with_jsonld else ""
    return (f'<html lang="{locale}"><head><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<meta name="robots" content="index, follow">'
            f'<link rel="canonical" href="{url}">{links}{blocks}</head>'
            '<body><h1>Produto</h1></body></html>').encode()


class LiveAuditParserTests(unittest.TestCase):
    def test_root_home_pt_es_hreflang(self):
        root = qa.BASE + "/"
        expected = {
            "pt-pt": qa.BASE + "/pt/",
            "es-es": qa.BASE + "/es/",
            "x-default": root,
        }
        self.assertEqual(qa.expected_hreflang(root), expected)
        self.assertEqual(qa.expected_hreflang(qa.BASE+"/pt/"), expected)
        self.assertEqual(qa.expected_hreflang(qa.BASE+"/es/"), expected)

    def test_valid_public_es_product(self):
        url = qa.BASE+"/es/products/hifu/"
        result = qa.evaluate_public_page(url, page(url, "es"))
        self.assertEqual(result["errors"], [])

    def test_missing_reciprocal_hreflang_detected(self):
        url = qa.BASE+"/pt/products/hifu/"
        html = page(url).replace(b'hreflang="es-es"', b'hreflang="not-es"')
        result = qa.evaluate_public_page(url, html)
        self.assertIn("hreflang_es-es_wrong_or_missing", result["errors"])

    def test_canonical_mismatch_detected(self):
        url = qa.BASE+"/pt/products/hifu/"
        html = page(url).replace(b'rel="canonical"', b'rel="ignored"')
        self.assertIn("canonical_missing_or_not_self", qa.evaluate_public_page(url, html)["errors"])

    def test_noindex_header_detected(self):
        url = qa.BASE+"/pt/products/hifu/"
        self.assertIn("noindex_on_public_sitemap_url",
                      qa.evaluate_public_page(url, page(url), "noindex")["errors"])

    def test_language_wrong_detected(self):
        url = qa.BASE+"/es/products/hifu/"
        self.assertIn("document_language_inconsistent_with_explicit_locale",
                      qa.evaluate_public_page(url, page(url, "pt-pt"))["errors"])

    def test_unprefixed_geo_english_is_warned_not_called_failing_locale(self):
        url = qa.BASE + "/products/hifu/"
        result = qa.evaluate_public_page(url, page(url, "en"))
        self.assertEqual(result["errors"], [])
        self.assertIn("unprefixed_geo_locale_not_pt_on_foreign_runner", result["warnings"])

    def test_jsonld_syntax_rejected(self):
        url = qa.BASE+"/pt/products/hifu/"
        html = page(url).replace(b'{"@type":"WebPage"}', b'{invalid json')
        self.assertIn("invalid_jsonld_syntax", qa.evaluate_public_page(url, html)["errors"])

    def test_institutional_no_hreflang_required(self):
        url = qa.BASE+"/privacidade/"
        self.assertEqual(qa.evaluate_public_page(url, page(url), "")["errors"], [])

    def test_google_specificity_overrides_first_match_allow(self):
        robots = "User-agent: *\nAllow: /\nDisallow: /go/\n"
        self.assertFalse(qa.googlebot_rule_for_this_site(robots, "/go/123"))
        self.assertTrue(qa.googlebot_rule_for_this_site(robots, "/pt/products/hifu/"))

    def test_google_tie_goes_to_allow(self):
        robots = "User-agent: *\nDisallow: /private/\nAllow: /private/\n"
        self.assertTrue(qa.googlebot_rule_for_this_site(robots, "/private/example"))

    def test_multiple_agents_fail_closed(self):
        robots = "User-agent: *\nAllow: /\nUser-agent: Googlebot\nDisallow: /\n"
        with self.assertRaisesRegex(ValueError, "user-agent groups"):
            qa.googlebot_rule_for_this_site(robots, "/pt/")

    def test_private_routes_are_never_fetched(self):
        sitemap = [qa.BASE+"/", qa.BASE+"/pt/", qa.BASE+"/es/"]
        robots = ("User-agent: *\nAllow: /\n" +
                  "".join(f"Disallow: {p}\n" for p in qa.EXPECTED_EXCLUSIONS))
        def fake_get(url):
            if url.endswith("/robots.txt"):
                return 200, url, robots.encode(), "text/plain", ""
            if url not in sitemap:
                raise AssertionError("Should not fetch private routes")
            return 200, url, page(url, "es" if "/es/" in url else "pt-pt"), "text/html", ""
        with patch.object(qa.core, "list_sitemap", return_value=sitemap), \
             patch.object(qa.core, "get", side_effect=fake_get), \
             patch.object(qa, "GOOGLEBOT_SAMPLES", ()), \
             patch.object(qa.time, "sleep", return_value=None):
            result = qa.perform({"id":"lowcost-europa","home":qa.BASE,"sitemap":qa.BASE+"/sitemap.xml"}, pause=0)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(len(result["private_robots"]), len(qa.EXPECTED_EXCLUSIONS))
        self.assertTrue(all(x["googlebot_disallowed"] for x in result["private_robots"]))


if __name__ == "__main__":
    unittest.main()
