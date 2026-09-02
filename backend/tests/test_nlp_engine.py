from pathlib import Path
import unittest

from app.nlp_engine import IncidentNlpEngine


class IncidentNlpEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        base = Path(__file__).resolve().parents[1]
        self.engine = IncidentNlpEngine(
            incidents_path=base / "data" / "incidents.csv",
            articles_path=base / "data" / "kb_articles.csv",
        )
        self.engine.load()

    def test_authentication_ticket_is_classified(self) -> None:
        result = self.engine.analyze("Cannot login to SAP after password reset")
        self.assertEqual(result.category, "Authentication")
        self.assertGreater(result.confidence, 0)
        self.assertTrue(result.similar_tickets)

    def test_vpn_ticket_retrieves_network_runbook(self) -> None:
        result = self.engine.analyze("Cisco VPN keeps disconnecting every few minutes")
        self.assertEqual(result.category, "Network")
        self.assertEqual(result.knowledge_articles[0].category, "Network")


if __name__ == "__main__":
    unittest.main()
