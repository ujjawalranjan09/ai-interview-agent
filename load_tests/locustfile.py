"""Locust load testing scenarios for AI Interview Agent."""
import random
from locust import HttpUser, task, between, tag


class InterviewAgentUser(HttpUser):
    """Simulates a user going through the interview workflow."""
    wait_time = between(1, 5)

    def on_start(self):
        """Login before starting tasks."""
        self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword",
        })

    @tag("interviews")
    @task(3)
    def list_interviews(self):
        self.client.get("/api/v1/interviews/")

    @tag("interviews")
    @task(2)
    def view_interview(self):
        self.client.get("/api/v1/interviews/sample-id")

    @tag("interviews")
    @task(1)
    def create_interview(self):
        self.client.post("/api/v1/interviews/", json={
            "candidate_name": f"Load Test Candidate {random.randint(1, 10000)}",
            "candidate_email": f"loadtest{random.randint(1, 10000)}@example.com",
            "position": "Software Engineer",
        })

    @tag("questions")
    @task(2)
    def list_questions(self):
        self.client.get("/api/v1/questions/")

    @tag("reports")
    @task(1)
    def view_report(self):
        self.client.get("/api/v1/reports/sample-id")

    @tag("auth")
    @task(1)
    def health_check(self):
        self.client.get("/api/v1/health")


class AnonymousUser(HttpUser):
    """Simulates unauthenticated traffic."""
    wait_time = between(0.5, 3)

    @tag("public")
    @task(1)
    def health_check(self):
        self.client.get("/api/v1/health")

    @tag("public")
    @task(1)
    def login_page(self):
        self.client.get("/api/v1/health/ready")
