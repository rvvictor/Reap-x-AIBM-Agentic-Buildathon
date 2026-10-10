# Bodega

Dynamic per-product stock targets for small businesses, and group purchasing through one global agent.

> Built for the **Reap x AIBM Agentic Buildathon** (Reap x AI Builders Mexico, 2026-10-09).
> All business data, sales history and savings figures are **simulated** and labeled `demo_data: true`.
> Reap is used in its **sandbox only**: no real money, no real cards.

## What it does

Small shops without distributor contracts keep a fixed stock level, so they either lose sales or tie up cash.
Bodega fixes both sides:

1. **Local agent (per business).** Computes a dynamic target stock per product from sales history,
   season and nearby events, and explains why (`reasons[]`, `confidence`).
2. **Global agent.** Groups the shortfalls of several businesses, compares suppliers by total delivered cost,
   and splits the savings so that every business pays less than it would alone.
3. **Control.** Each owner approves their own share within a budget cap. The agent never sees card data
   and stops to ask for approval when a quote expires or stock runs out.

The LLM never produces the key numbers. It only turns events and weather into schema-validated signals
and writes explanations. Targets, savings and allocation are deterministic, tested code.

## Run the demo (no keys, no network)

Requirements: [uv](https://docs.astral.sh/uv/) and Node.js.

```bash
cp .env.example .env            # DEMO_MODE defaults to true; no secrets needed
uv sync
npm --prefix web ci
npm --prefix web run build
uv run uvicorn app.main:app --port 8000
```

Open <http://localhost:8000>. FastAPI serves the built frontend and the API from one process.

With `DEMO_MODE=true` nothing calls Reap or an LLM: recorded responses from `app/fixtures/` are used.

### Development

```bash
uv run uvicorn app.main:app --reload --port 8000
npm --prefix web run dev        # http://localhost:5173, /api is proxied to FastAPI
```

Inside a UAK worktree the ports are `$UAK_PORT` (API) and `$UAK_PORT+1` (web).

## Configuration

Read from `.env` (git-ignored). Never commit keys. See `.env.example`.

| Variable | Purpose |
|---|---|
| `DEMO_MODE` | `true` (default): recorded fixtures, no network |
| `REAP_API_KEY` | Reap sandbox key, only needed with `DEMO_MODE=false` |
| `REAP_BASE_URL` | Defaults to `https://sandbox.api.reap.global` |
| `REAP_VERSION` | `Reap-Version` header; the client falls back to `2025-02-14` |
| `REAP_RETURN_URL` | HTTPS return URL required by Reap checkout |
| `ANTHROPIC_API_KEY` | Only for live signal extraction |

The model ID is pinned in one place: `app/config.py`.

## The 6-step flow

| # | Step | Endpoint | Status |
|---|---|---|---|
| 1 | Pick a business, see base vs current stock | `GET /api/businesses/{id}/inventory` | UI with mock data only |
| 2 | Predict stock: dynamic target, reasons, confidence | `POST /api/businesses/{id}/forecast` | Implemented |
| 3 | Detect shortfalls across the 4 businesses | `POST /api/needs/publish` | Pending |
| 4 | Global agent: supplier comparison and per-business savings | `POST /api/global/proposals` | In progress |
| 5 | Each owner approves their share; sandbox checkout | `POST /api/global/proposals/{id}/approve` | Pending |
| 6 | Quote expires or stock runs out: recalculate or stop | `POST /api/global/proposals/{id}/recheck` | Pending (P1) |

Signals (`GET /api/signals`, `POST /api/signals/extract`) feed step 2. Status reflects the repo when this
was written; the source of truth is `uak status`.

## Reap integration

Search, quote and checkout use the Reap Agentic API sandbox (`app/integrations/reap/`). Without a key the
sandbox answers `401 INVALID_AUTH_HEADER`; those responses are recorded in `app/fixtures/reap/` and replayed in
`DEMO_MODE`. A completed sandbox checkout has **not** been observed yet. Details in `docs/REAP-NOTES.md`.

Volume pricing is not verified in Reap, so price tiers in the demo are simulated and labeled `demo_data`.

## Tests

```bash
uv run pytest -q
bash .uak/bin/smoke             # ruff + pytest + web lint + web build
```

## Screenshots

Pending: they must be captured from the running app once steps 3-5 are integrated. See `docs/DEMO.md`.

## Layout

```
app/            FastAPI: config, routers (auto-discovered), services, schemas, fixtures, integrations/reap
web/            React + Vite; features under web/src/features/* are auto-discovered
docs/           Idea, Reap notes, demo script
e2e/            End-to-end run of the demo flow
```

## Scope

Out of scope: businesses with distributor contracts, own logistics, recurring charges (mandates are not
available), real purchases, complex perishables, travel and restricted categories.
