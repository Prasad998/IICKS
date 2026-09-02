import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiTest(unittest.TestCase):
    def test_health_reports_pipeline_components(self) -> None:
        with TestClient(app) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["incidents_loaded"], 1000)
        self.assertEqual(payload["articles_loaded"], 1000)
        self.assertEqual(payload["model_backend"], "tfidf-local")
        self.assertIn("redis_cache", payload)
        self.assertIn("kafka_events", payload)

    def test_submit_accepts_async_kafka_request(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/submit",
                json={
                    "description": "Payroll batch job failed overnight with database timeout",
                    "top_k": 5,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["request_id"])
        self.assertEqual(payload["kafka_topic"], "incident.requests")


if __name__ == "__main__":
    unittest.main()
