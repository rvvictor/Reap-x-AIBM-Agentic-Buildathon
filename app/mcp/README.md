# Bodega MCP bridge

Run from the repository root using the locked MCP 2.3 SDK:

```sh
uv sync --locked
DEMO_MODE=true uv run python -m app.mcp
```

The server uses stdio, not a TCP port. A trusted global coordinator launches
one process and publishes the local agents' minimal needs into that process.
Only MCP protocol messages go to stdout. Use an MCP client, not an interactive
shell, to exchange messages after starting it.

Tools:

| Tool | Arguments | Result |
| --- | --- | --- |
| `publicar_faltas` | `faltas: Need[]` (1–100) | received/pending counts, `demo_data` |
| `consultar_ofertas` | optional `category` | canonical simulated `offers[]`, `demo_data` |
| `proponer_compra` | none | canonical `proposals[]`, `demo_data` |

`Need` contains `business_id`, `sku_id`, `product_name`, `category`, `qty`,
`needed_by` (ISO date) and optional `accepted_equivalents`. Values must match
the canonical fixture catalog, including exact product names. Sales, margins,
recipes and extra fields are rejected. Publications are atomic and replace
the same business/SKU on replay. There are at most 100 pending needs.

All tools require `DEMO_MODE=true`. This is a trusted global-coordinator
interface: it returns cross-business allocations and has no caller identity
or tenant authentication. Do not expose it to external or untrusted clients.
Each launcher has independent in-memory state; restarting clears it. This
does not create a shared durable queue between separate MCP processes.
Proposals reuse the global agent's validation, budgets and delivered-price
calculation. All offers/drafts are simulated; nothing authorizes checkout,
enrolls a business or sends a payment.

## Direct HTTP fallback

If the MCP host cannot launch stdio, the coordinator keeps the validated
`Need[]` and submits `{"needs": [...]}` directly to
`POST /api/global/proposals` on the API's configured `$UAK_PORT`.
The HTTP response is `Proposal[]` (not the MCP result envelope).
There is no HTTP needs-publication route; do not invent one. This fallback
also requires demo mode and retains no MCP queue. Run the API normally:

```sh
DEMO_MODE=true uv run uvicorn app.main:app --host 127.0.0.1 --port "$UAK_PORT"
```

Verification: `uv run pytest -q app/tests/test_mcp.py` launches a real MCP
subprocess, negotiates the lifecycle, lists all three tools, publishes a
local need and checks the global proposal, replay, process isolation,
invalid/private input, batch limits and live-mode rejection.
