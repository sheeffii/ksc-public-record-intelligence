# tests/

| Directory      | What lives here                                                     | Runner             |
| -------------- | ------------------------------------------------------------------- | ------------------ |
| `unit/`        | Backend unit tests — no infrastructure                              | `pytest`           |
| `integration/` | Backend tests against live PostgreSQL/pgvector, Redis, MinIO        | `pytest` (+ infra) |
| `e2e/`         | Playwright browser tests against a running stack                    | `pnpm e2e`         |
| `fixtures/`    | Reserved: small, public, hand-checked record fixtures (later phase) | —                  |
| `evaluation/`  | Reserved: citation-accuracy and neutrality evaluation sets (later)  | —                  |

Frontend unit/component tests are colocated in `apps/web/src/**/*.test.tsx` (Vitest).

No fixture may contain a real protected-witness identity or any text not in the public record.
