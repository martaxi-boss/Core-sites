import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import seo_growth_core as core


class SeoGrowthCoreTests(unittest.TestCase):
    def test_enforces_canonical_host_and_protocol(self):
        self.assertEqual(
            core.safe_url("/pt/", "www.lowcost-europa.eu", "https://www.lowcost-europa.eu/"),
            "https://www.lowcost-europa.eu/pt/",
        )
        self.assertIsNone(core.safe_url("https://other.example/pt/", "www.lowcost-europa.eu"))
        self.assertIsNone(core.safe_url("http://www.lowcost-europa.eu/", "www.lowcost-europa.eu"))
        self.assertIsNone(core.safe_url("https://www.lowcost-europa.eu:8080/", "www.lowcost-europa.eu"))

    def test_prevents_cross_host_redirects(self):
        from email.message import Message
        req = core.Request("https://example.com/robots.txt")
        redirect = core.SameHostRedirect()
        self.assertIsNotNone(
            redirect.redirect_request(req, None, 302, "Found", Message(), "https://example.com/robots-new.txt")
        )
        with self.assertRaises(ValueError):
            redirect.redirect_request(req, None, 302, "Found", Message(), "http://127.0.0.1/internal")

    def test_parses_sitemaps(self):
        xml = b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://sevelora.eu/</loc></url></urlset>'
        kind, urls = core.xml_locs(xml)
        self.assertEqual(kind, "urlset")
        self.assertEqual(urls, ["https://sevelora.eu/"])

    def test_extracts_content_and_outgoing_links(self):
        p = core.PageParser()
        p.feed('<html><head><title>Guia HIFU</title><meta name="description" content="Guia de compra">'
               '<link rel="canonical" href="https://sevelora.eu/guia"></head>'
               '<body><h1>Como escolher</h1><img src="/a.jpg"><a href="/produtos">Produtos</a>'
               '<script type="application/ld+json">{"@type":"Article"}</script></body></html>')
        self.assertEqual(p.title, "Guia HIFU")
        self.assertEqual(p.h1, ["Como escolher"])
        self.assertEqual(p.description, "Guia de compra")
        self.assertEqual(p.missing_image_alt, 1)
        self.assertTrue(p.structured_data)
        self.assertIn("/produtos", p.links)
        self.assertNotIn("@type", " ".join(p.text))

    def test_core_suggests_buyer_content_without_creating_visits(self):
        site = {
            "id": "example", "home": "https://example.com", "sitemap": "https://example.com/sitemap.xml",
            "max_pages": 20, "focus_path_contains": ["/categoria/"],
        }
        home = ("<html><title>Inicio</title><meta name='description' content='A loja'>"
                "<link rel='canonical' href='https://example.com/'><h1>Inicio</h1>"
                "<a href='/categoria/teste'>Ver</a></html>").encode()
        category = ("<html><title>Teste</title><meta name='description' content='Descricao'>"
                    "<link rel='canonical' href='https://example.com/categoria/teste'>"
                    "<h1>Teste</h1><p>Descricao</p></html>").encode()
        def stub_get(url):
            if url == "https://example.com/":
                return 200, url, home, "text/html"
            if url == "https://example.com/categoria/teste":
                return 200, url, category, "text/html"
            raise AssertionError(url)

        class AllowRobots:
            def can_fetch(self, user_agent, url):
                return True

        with patch.object(core, "list_sitemap", return_value=["https://example.com/", "https://example.com/categoria/teste"]), \
             patch.object(core, "robot_policy", return_value=(AllowRobots(), None)), \
             patch.object(core, "get", side_effect=stub_get):
            report = core.audit(site, pause=0)
        self.assertEqual(report["pages_scanned"], 2)
        self.assertEqual(len(report["growth_opportunities"]), 1)
        self.assertEqual(report["growth_opportunities"][0]["incoming_links"], 1)
        self.assertIn("does not generate fake users", core.markdown(report))


    def test_rich_commercial_pages_are_not_flagged_for_more_guides(self):
        site = {"id": "lowcost-europa", "home": "https://example.com",
                "sitemap": "https://example.com/sitemap.xml",
                "max_pages": 10, "focus_path_contains": ["/products/"]}
        urls = ["https://example.com/", "https://example.com/products/hifu/",
                "https://example.com/pt/products/hifu/"]
        class Robots:
            def can_fetch(self, user_agent, url):
                return True
        def html_for(url):
            links = "".join(f'<a href="{p}">Produto</a>' for p in urls[1:])
            return (f'<html><title>HIFU profissional</title>'
                    f'<meta name="description" content="Como escolher produtos HIFU">'
                    f'<link rel="canonical" href="{url}"><h1>HIFU profissional</h1>'
                    f'<main>{links}<h2>Critérios de escolha</h2>'
                    + " comparar equipamentos " * 420 + "</main></html>").encode()
        with patch.object(core, "list_sitemap", return_value=urls), \\
             patch.object(core, "robot_policy", return_value=(Robots(), None)), \\
             patch.object(core, "get", side_effect=lambda url: (200, url, html_for(url), "text/html")):
            report = core.audit(site, pause=0)
        self.assertFalse(report["partial_scan"])
        self.assertEqual(report["pages_scanned"], 3)
        self.assertEqual(report["commercial_pages_scanned"], 2)
        self.assertEqual(report["growth_opportunities"], [])

    def test_blocked_sitemap_page_marks_scan_partial(self):
        site = {"id": "lowcost-europa", "home": "https://example.com",
                "sitemap": "https://example.com/sitemap.xml",
                "max_pages": 10, "focus_path_contains": ["/products/"]}
        urls = ["https://example.com/", "https://example.com/pt/",
                "https://example.com/products/hifu/"]
        class Robots:
            def can_fetch(self, agent, url):
                return "/products/" not in url
        def html_for(url):
            return (f'<html><title>Produto</title><meta name="description" content="teste">'
                    f'<link rel="canonical" href="{url}"><h1>Produto</h1></html>').encode()
        with patch.object(core, "list_sitemap", return_value=urls), \\
             patch.object(core, "robot_policy", return_value=(Robots(), None)), \\
             patch.object(core, "get", side_effect=lambda url: (200, url, html_for(url), "text/html")):
            report = core.audit(site, pause=0)
        self.assertTrue(report["partial_scan"])
        self.assertEqual(report["pages_scanned"], 2)
        self.assertEqual(report["pages_skipped"], 1)


if __name__ == "__main__":
    unittest.main()
