# tests/

| Directory      | What lives here                                                     | Runner             |
| -------------- | ------------------------------------------------------------------- | ------------------ |
| `unit/`        | Backend unit tests — no infrastructure                              | `pytest`           |
| `integration/` | Backend tests against live PostgreSQL/pgvector, Redis, MinIO        | `pytest` (+ infra) |
| `e2e/`         | Playwright browser tests against a running stack                    | `pnpm e2e`         |
| `fixtures/`    | Reserved: small, public, hand-checked record fixtures (later phase) | —                  |
| `evaluation/`  | Reserved: citation-accuracy and neutrality evaluation sets (later)  | —                  |

Frontend unit/component tests are colocated in `apps/web/src/**/*.test.tsx` (Vitest).

Integration tests load the synthetic `KSC-DEMO-0000` fixture
(`apps/api/src/ksc_api/fixtures/demo.py`) into the throwaway `ksc_test` database;
`test_migrations.py` also downgrades to base and back, so it runs last and other
tests reload what they need. The frontend `ApiRepository` tests use a stubbed
`fetch` with the same shapes (`apps/web/src/data/api/fixtures.ts`).

No fixture may contain a real protected-witness identity or any text not in the public record.
