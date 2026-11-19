import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from growth_engine.gsc import GscRow, load_csv, page_opportunities
from growth_engine.privacy import redact_report
from growth_engine.planner import technical_queue, commercial_briefs, markdown, plan, suggest_internal_source
import seo_growth_core as core


def sample_report():
    home = "https://sevelora.eu/"
    cat = "https://sevelora.eu/categoria/anal"
    return {
        "site": "sevelora", "home": home,
        "checked_at_utc": "2026-11-19T18:00:00+00:00",
        "sitemap_urls": 2, "pages_scanned": 2, "partial_scan": False,
        "findings": [
            {"level": "important", "url": cat, "problem": "Missing meta description",
             "recommendation": "Write a distinctive description"},
            {"level": "important", "url": cat, "problem": "Duplicate description among scanned pages",
             "recommendation": "Differentiate"},
            {"level": "opportunity", "url": cat, "problem": "Some images lack alt text",
             "recommendation": "Add accurate alt text"},
        ],
        "page_signals": [
            {"url": home, "title": "Sevelora | Catálogo", "words": 200,
             "outbound_internal": [], "incoming_links": 0},
            {"url": cat, "title": "Artigos para Adultos | Anal", "words": 75,
             "outbound_internal": [], "incoming_links": 0},
        ],
        "growth_opportunities": [
            {"url": cat, "title": "Artigos para Adultos | Anal", "incoming_links": 0,
             "suggestion": "More useful buyer information"},
        ],
    }


class GscTests(unittest.TestCase):
    def test_import_english_and_filter_different_host(self):
        csv = ('Page,Query,Clicks,Impressions,CTR,Position,Country\n'
               'https://sevelora.eu/categoria/anal,escolher produto,1,120,0.83%,8.5,prt\n'
               'https://other.invalid/p,codigo,2,100,2%,5,prt\n'
               'https://sevelora.eu/categoria/anal,other,50,10,500%,5,prt\n')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "data.csv"
            path.write_text(csv, encoding="utf-8")
            rows, info = load_csv(path, "sevelora.eu", country_filter="prt")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].impressions, 120)
        self.assertEqual(info["rows_rejected"], 2)
        opportunities = page_opportunities(rows, {"https://sevelora.eu/categoria/anal"})
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0]["clicks"], 1)

    def test_import_semicolon_portuguese_decimal_comma(self):
        csv = ('Página;Consulta;Cliques;Impressões;Posição;País\n'
               'https://sevelora.eu/categoria/anal;exemplo de pesquisa;0;101;12,4;prt\n')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "data.csv"
            path.write_text(csv, encoding="utf-8-sig")
            rows, info = load_csv(path, "sevelora.eu")
        self.assertEqual(rows[0].position, 12.4)
        self.assertEqual(rows[0].impressions, 101)

    def test_rejects_export_missing_joint_dimensions(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "data.csv"
            path.write_text('Query,Clicks,Impressions,Position\nabc,0,5,9\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Joint page"):
                load_csv(path, "sevelora.eu")

    def test_country_filter_rejects_csv_with_no_country_dimension(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "global.csv"
            path.write_text(
                "Page,Query,Clicks,Impressions,Position\n"
                "https://sevelora.eu/p,example,0,100,8\n",
                encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "Country column"):
                load_csv(path, "sevelora.eu", country_filter="pt")

    def test_country_filter_drops_empty_country(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "countries.csv"
            path.write_text(
                "Page,Query,Clicks,Impressions,Position,Country\n"
                "https://sevelora.eu/p,example,0,100,8,\n"
                "https://sevelora.eu/p,example2,0,100,8,prt\n",
                encoding="utf-8"
            )
            rows, info = load_csv(path, "sevelora.eu", country_filter="pt")
        self.assertEqual(len(rows), 1)
        self.assertEqual(info["rows_rejected"], 1)

    def test_small_or_high_ctr_not_marked_as_growth_opportunity(self):
        rows = [
            GscRow("https://sevelora.eu/p", "tiny", 0, 5, 8),
            GscRow("https://sevelora.eu/p", "high ctr", 10, 50, 8),
            GscRow("https://sevelora.eu/p", "low", 0, 40, 10),
        ]
        q = page_opportunities(rows, {"https://sevelora.eu/p"})
        self.assertEqual([x["query"] for x in q], ["low"])


class PlannerTests(unittest.TestCase):
    def test_prioritization_bounded_per_url(self):
        queue = technical_queue(sample_report())
        self.assertEqual(len(queue), 2)
        self.assertEqual(queue[0]["priority"], "P1")

    def test_brief_in_portuguese_and_site_specific(self):
        briefs = commercial_briefs(sample_report(), {"id": "sevelora"}, limit=2)
        self.assertEqual(len(briefs), 1)
        self.assertEqual(briefs[0]["state"], "proposal_only")
        self.assertTrue(any("higiene" in s.lower() for s in briefs[0]["suggested_sections"]))
        self.assertEqual(briefs[0]["internal_link_suggestion"]["source"], "https://sevelora.eu/")

    def test_gsc_queries_redacted_from_public_markdown(self):
        rows = [GscRow("https://sevelora.eu/categoria/anal", "minha-pesquisa-confidencial", 0, 500, 7)]
        result = plan(sample_report(), {"id": "sevelora"}, rows)
        self.assertEqual(result["gsc"]["status"], "provided_export")
        public = markdown(result, public=True)
        private = markdown(result, public=False)
        self.assertNotIn("minha-pesquisa-confidencial", public)
        self.assertIn("minha-pesquisa-confidencial", private)

    def test_no_metrics_claimed_without_real_gsc_data(self):
        result = plan(sample_report(), {"id": "sevelora"})
        self.assertEqual(result["gsc"]["status"], "not_connected")
        self.assertEqual(result["guardrails"]["traffic_policy"], "no_synthetic_clicks_or_visitors")
        self.assertNotIn("Pesquisa observada:", markdown(result))

    def test_public_json_redacts_gsc_query_and_metrics(self):
        rows = [GscRow("https://sevelora.eu/categoria/anal", "privado-muito-identificavel", 0, 348, 9)]
        result = plan(sample_report(), {"id": "sevelora"}, rows,
                      {"rows_accepted": 1, "rows_rejected": 0})
        raw = json.dumps(result, ensure_ascii=False)
        self.assertIn("privado-muito-identificavel", raw)
        clean = redact_report(result)
        public = json.dumps(clean, ensure_ascii=False)
        self.assertNotIn("privado-muito-identificavel", public)
        self.assertNotIn("348 impressões", public)
        self.assertEqual(clean["briefs"][0]["gsc_query"], None)
        self.assertEqual(result["briefs"][0]["gsc_query"], "privado-muito-identificavel")
        self.assertIn("omitidas", clean["briefs"][0]["why"])

    def test_no_content_gaps_means_no_bogus_briefs(self):
        report = sample_report()
        report["growth_opportunities"] = []
        for item in report["page_signals"]:
            item["words"] = 1100
            item["incoming_links"] = 5
        self.assertEqual(commercial_briefs(report, {"id": "sevelora"}), [])

    def test_gsc_demand_reveals_rich_page_opportunity(self):
        report = sample_report()
        report["growth_opportunities"] = []
        for item in report["page_signals"]:
            item["words"] = 1000
            item["incoming_links"] = 5
        rows = [GscRow("https://sevelora.eu/categoria/anal", "pesquisa reais testes", 0, 200, 9)]
        briefs = commercial_briefs(report, {"id": "sevelora", "focus_path_contains": ["/categoria/"]}, rows)
        self.assertEqual(len(briefs), 1)
        self.assertEqual(briefs[0]["gsc_query"], "pesquisa reais testes")

    def test_categories_first_without_real_search_demand(self):
        report = sample_report()
        product = "https://sevelora.eu/produto/123"
        report["page_signals"].append({
            "url": product, "title": "Produto Sevelora X", "words": 12,
            "outbound_internal": [], "incoming_links": 0
        })
        report["growth_opportunities"].insert(0, {
            "url": product, "title": "Produto Sevelora X", "incoming_links": 0,
            "suggestion": "review"
        })
        briefs = commercial_briefs(report, {"id": "sevelora"}, limit=2)
        self.assertEqual(briefs[0]["url"], "https://sevelora.eu/categoria/anal")

    def test_cannot_suggest_same_page_in_another_locale(self):
        target = {
            "url": "https://www.lowcost-europa.eu/products/hifu/",
            "title": "HIFU profissional"
        }
        pages = [
            target,
            {"url": "https://www.lowcost-europa.eu/pt/products/hifu/",
             "title": "HIFU profissional", "outbound_internal": []},
            {"url": "https://www.lowcost-europa.eu/pt/",
             "title": "HIFU equipamentos", "outbound_internal": []}
        ]
        suggestion = suggest_internal_source(target, pages)
        self.assertEqual(suggestion["source"], "https://www.lowcost-europa.eu/pt/")

    def test_does_not_link_across_language_versions(self):
        target = {"url": "https://www.lowcost-europa.eu/pt/products/hifu/", "title": "HIFU profissional"}
        pages = [
            target,
            {"url": "https://www.lowcost-europa.eu/es/products/hifu/", "title": "HIFU profesional", "outbound_internal": []},
            {"url": "https://www.lowcost-europa.eu/pt/", "title": "HIFU inicial", "outbound_internal": []},
        ]
        source = suggest_internal_source(target, pages)
        self.assertEqual(source["source"], "https://www.lowcost-europa.eu/pt/")

    def test_does_not_report_orphans_on_partial_crawl(self):
        site = {"id": "test", "home": "https://example.com",
                "sitemap": "https://example.com/sitemap.xml",
                "focus_path_contains": ["/p/"], "max_pages": 3}
        all_pages = ["https://example.com/", "https://example.com/p/a",
                     "https://example.com/p/b", "https://example.com/p/c"]
        pages_html = '<html><title>A</title><meta name="description" content="x"><link rel="canonical" href="{}"><h1>A</h1></html>'
        class Robots:
            def can_fetch(self, *args):
                return True
        from unittest.mock import patch
        def fake_get(url):
            return 200, url, pages_html.format(url).encode(), "text/html", ""
        with patch.object(core, "list_sitemap", return_value=all_pages), \
             patch.object(core, "robot_policy", return_value=(Robots(), None)), \
             patch.object(core, "get", side_effect=fake_get):
            report = core.audit(site, pause=0)
        self.assertTrue(report["partial_scan"])
        self.assertEqual(len(report["page_signals"]), 3)
        self.assertFalse(any("No incoming links" in x["problem"] for x in report["findings"]))


if __name__ == "__main__":
    unittest.main()
