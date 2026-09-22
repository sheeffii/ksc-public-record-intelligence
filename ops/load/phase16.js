import http from "k6/http";
import { check, sleep } from "k6";

const base = __ENV.BASE_URL;
const caseId = __ENV.CASE_ID || "KSC-BC-2020-06";

export const options = {
  scenarios: {
    beta_readers: {
      executor: "ramping-vus",
      stages: [
        { duration: "30s", target: 10 },
        { duration: "2m", target: 10 },
        { duration: "30s", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<1000"],
  },
};

const routes = [
  "/",
  "/search?q=F00001",
  "/documents",
  `/network?case=${caseId}`,
  `/timeline?case=${caseId}`,
  __ENV.READER_PATH,
  __ENV.FINDING_PATH,
  __ENV.APPEAL_PATH,
  __ENV.AI_PATH,
].filter(Boolean);

export default function () {
  for (const route of routes) {
    const response = http.get(`${base}${route}`, { tags: { route } });
    check(response, {
      [`${route} returned 2xx`]: (value) => value.status >= 200 && value.status < 300,
    });
  }
  sleep(1);
}
