# Beta performance and accessibility targets

On the realistic staging corpus, home, search, reader, network, timeline,
finding detail and appeal research target server response p95 under 1 second and
less than 1% HTTP errors at 10 concurrent beta users. AI research targets p95
under 30 seconds with an explicit progress state; provider timeout remains 30
seconds. Run `k6 run -e BASE_URL=https://staging.example ops/load/phase16.js`
and retain k6 p50/p95/error output plus DB CPU/connections, storage latency and
API resource graphs. Supply real held-record paths through `READER_PATH`,
`FINDING_PATH`, `APPEAL_PATH` and `AI_PATH`; do not invent identifiers. These
are targets, not claimed measurements.

The final audit covers keyboard-only completion, visible focus, heading order,
names/labels, dialog focus, contrast, 200% zoom and mobile layouts for home,
search, reader, network textual alternative, timeline, finding, appeal and AI.
Run the Playwright axe check in both desktop and mobile projects, then complete
the manual list because automation cannot establish workflow usability.
