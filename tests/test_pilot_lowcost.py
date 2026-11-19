import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LowCostPilotConfigurationTests(unittest.TestCase):
    def test_only_lowcost_is_scheduled_for_the_pilot(self):
        config = json.loads((ROOT / "sites.json").read_text(encoding="utf-8"))
        sites = config["sites"]
        self.assertEqual(len(sites), 1)
        self.assertEqual(sites[0]["id"], "lowcost-europa")
        self.assertEqual(sites[0]["home"], "https://www.lowcost-europa.eu")
        self.assertEqual(sites[0]["sitemap"], "https://www.lowcost-europa.eu/sitemap.xml")
        self.assertEqual(sites[0]["focus_path_contains"], ["/products/"])
        self.assertNotIn("sevelora.eu", json.dumps(config).lower())

    def test_manual_performance_test_is_also_lowcost_only(self):
        workflow = (ROOT / ".github/workflows/seo-performance-sample.yml").read_text(encoding="utf-8")
        self.assertIn("https://www.lowcost-europa.eu/pt/", workflow)
        self.assertNotIn("sevelora.eu", workflow)


if __name__ == "__main__":
    unittest.main()
