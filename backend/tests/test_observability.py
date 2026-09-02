import unittest

from fastapi.testclient import TestClient

from app.main import app


class ObservabilityTest(unittest.TestCase):
    def test_evaluate_returns_classification_metrics(self) -> None:
        with TestClient(app) as client:
            response = client.post("/api/evaluate", json={"test_ratio": 0.2})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("accuracy", payload)
        self.assertIn("confusion_matrix", payload)
        self.assertIn("class_metrics", payload)
        self.assertGreaterEqual(payload["test_size"], 1)

    def test_metrics_endpoint_exposes_prometheus_text(self) -> None:
        with TestClient(app) as client:
            response = client.get("/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertIn("incident_api_requests_total", response.text)
        self.assertIn("incident_api_request_duration_seconds", response.text)


if __name__ == "__main__":
    unittest.main()
