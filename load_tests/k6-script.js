import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const errorRate = new Rate("errors");
const interviewTrend = new Trend("interview_duration");

export const options = {
  stages: [
    { duration: "2m", target: 50 },
    { duration: "5m", target: 50 },
    { duration: "2m", target: 100 },
    { duration: "5m", target: 100 },
    { duration: "2m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],
    errors: ["rate<0.05"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  const responses = http.batch([
    ["GET", `${BASE_URL}/api/v1/health`],
    ["GET", `${BASE_URL}/api/v1/health/ready`],
  ]);

  responses.forEach((res) => {
    check(res, {
      "status is 200": (r) => r.status === 200,
    });
    errorRate.add(res.status !== 200);
  });

  sleep(Math.random() * 3 + 1);
}
