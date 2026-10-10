# Reap sandbox notes (HACK-003)

## Version and host

`Reap-Version` current value is `2025-02-14` (format `YYYY-MM-DD`).

Source: [API reference overview](https://docs.reap.global/api-reference/overview), header table "Current version: 2025-02-14". The OpenAPI enum for `POST /agentic/products/search` lists the same single value.

Sandbox base used by this client: `https://sandbox.api.reap.global` (documented alias of the Singapore sandbox). HACK-001 reads the same names from `.env`: `REAP_BASE_URL`, `REAP_API_KEY`, `REAP_VERSION`, `DEMO_MODE`, `REAP_RETURN_URL`.

If `REAP_VERSION` is empty, the client sends `2025-02-14`.

## Headers

| Header | Where |
|---|---|
| `Authorization: Bearer <REAP_API_KEY>` | Every live call. The key is read only from the environment. An empty key raises `ReapConfigError` and does not send a request. |
| `Reap-Version` | Every live call. |
| `Idempotency-Key` | `POST /agentic/quotes` and `POST /agentic/checkouts`. Search does not require it in the OpenAPI parameters. |
| `X-Simulate-Checkout: COMPLETED` | Checkout only. Sandbox header from [one-time purchases](https://docs.reap.global/agentic-payments/one-time-purchases). |

## Coffee search

`POST /agentic/products/search` has `query`, not a category filter. The request query is `coffee`. `Coffee & Tea` is the merchant vertical in the event brief (17 supported merchants); it is not a field on this endpoint.

Context sent: `country=US`, `currency=USD`, `availability=AVAILABLE_ONLY`.

## Live sandbox on 2026-10-10

No `.env` and no `REAP_API_KEY` on this machine. Probes used an empty bearer token. Responses are stored as recorded errors (`blocked: true`, `demo_data: false`), not as a successful catalog.

| Call | Result |
|---|---|
| `POST /agentic/products/search` query `coffee` | `401` `INVALID_AUTH_HEADER` / `Invalid Authorization header format` |
| `POST /agentic/quotes` | `401` `INVALID_AUTH_HEADER` |
| `POST /agentic/checkouts` with non-UUID ids | `422` `VALIDATION_FAILED`: `quoteId` and `enrollmentId` must be UUIDs |
| `POST /agentic/checkouts` with UUID ids, `Idempotency-Key`, and `X-Simulate-Checkout: COMPLETED` | `401` `INVALID_AUTH_HEADER` |

`DEMO_MODE=true` (the default) returns `app/fixtures/reap/search_coffee.json`, `quote.json`, and `checkout.json` and does not call the network. A completed checkout was not observed.

## Smoke

`bash .uak/bin/smoke` needs `.uak/bin/smoke-project`, owned by HACK-001 (in review, not on this branch). This task does not add that file.
