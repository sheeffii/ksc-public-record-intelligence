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

## Blocker-resolution result — 2026-09-23

The original 10-VU, three-minute run failed: 1,323 requests, 0.00% errors,
p50 755.43 ms and p95 2.85 s. Targeted concurrent profiling isolated the home
route at p95 2.63 s: each request fanned out to seven full repository reads plus
the ingestion status read. Finding detail and appeal subsequently measured p95
1.15 s and 1.08 s when included in the expanded representative run. Read-only
home, finding and appeal projections now use a 30-second server cache; no target
or load shape was weakened.

The final run covered `/`, search, documents, network, timeline, the held
`F00001` reader, finding `FD-F03752-P12-16`, appeal and AI. At 10 VUs it passed
all global and per-route thresholds: 5,940 requests, 0 errors, p50 75.18 ms and
p95 467.66 ms. Per-route p95 values in route order were 59.65, 578.38, 406.68,
732.08, 328.94, 473.80, 62.90, 60.79 and 333.10 ms. The earlier resource
baseline was approximately 64% web, 119% API and 39% PostgreSQL CPU; no service
or database error occurred in the final run.

The manual accessibility review passed the key workflows on desktop, a
720-pixel layout equivalent to 200% browser zoom, and a 412×915 representative
mobile viewport. Keyboard skip navigation, visible focus, command-dialog focus
entry/trap/Escape/return, the mobile reader research panel, and horizontal
reflow all passed. Representative contrast ratios were 16.30:1 for the main
heading, 6.89:1 for body copy and 6.10:1 for the primary button. The review
found and fixed the command palette's missing focus trap and focus restoration.
The recorded 18/18 automated axe routes and 38/38 desktop/mobile workflows
remain the automated baseline.
