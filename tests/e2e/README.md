# Actual DEMO_MODE E2E coverage (HACK-019)

Run from the task worktree with its `.uak-env` / `UAK_PORT`. Installation,
browser execution and smoke must use the coordinator's exclusive machine turn.
Prepare `uv sync --locked`, `npm --prefix web ci`, and
`uv run playwright install chromium`, then run the exact task Verify:

```sh
uv run pytest -q tests/e2e
```

On Windows export `PYTHONUTF8=1` for the full product smoke. Two pre-existing
pharmacy tests read UTF-8 fixture files without specifying the encoding;
requesting their owner to make those reads portable does not change this task's
scope. HACK-019's own JSON fixture reads explicitly use UTF-8.

The suite builds the current web sources, starts the real FastAPI app on the
task port and closes only its own subprocess. Each test starts a fresh server
to isolate process-local proposals, enrollments and ledgers. DEMO_MODE is forced
true with empty Reap/Anthropic key variables. No API response interception,
dependency replacements, fabricated successful orders or external API calls
are used. Reap's application-level demo adapter is the actual shipped behavior;
its simulated order is not evidence of a successful external sandbox payment.

## Coverage and missing acceptance criteria

| Original flow step | Actual coverage / limitation |
| --- | --- |
| 1. Select business and inspect inventory | Browser checks the existing fixed five-product Aurora screen and its `demo_data` label. Business selection and inventory API are not implemented in the current UI. |
| 2. Predict product stock | Real forecast HTTP requests consume canonical four-cafe inventory and sales fixtures, with recorded demo signals. The inventory screen does not invoke this endpoint. |
| 3. Publish shortages | Shortages are computed from the actual forecast responses and sent to the real global HTTP fallback documented in `app/mcp/README.md`. No HTTP `/needs/publish` exists. This test does not claim browser/MCP publication. |
| 4. Compare group proposal | Browser selects API mode, recalculates the UI's own example basket and checks the actual proposal response. This basket is not connected to step 2's derived shortages. |
| 5. Authorize and pay | Real browser clicks all four server authorizations, enrolls and confirms ACTIVE, performs one DEMO_MODE checkout and waits for the reconciled server ledger. It checks amount, budget caps, final order, authoritative read and replay after reload. |
| 6. Stockout / expired quote and reapproval | **Blocked:** no public recheck endpoint or UI action exists. `/api/global/proposals/{id}/recheck` is not implemented. Expiry behavior in payment unit tests does not establish an E2E step. Duplicate checkout prevention is tested separately and does not substitute for this step. |

**The original six-step acceptance criterion remains incomplete.** These tests
provide regression coverage for available behavior without portraying separate
API and browser paths as one connected six-step workflow. The API request date
comes from the recorded sales; its `needed_by=2099-01-01` is an explicit synthetic
delivery deadline, not an observed real-world forecast.

Each UI case uses `prefers-reduced-motion: reduce`, waits for final ledger/UI
state and captures its viewport at 1280×720 and 390×844 into `artifacts/`.
Screenshots are generated only by a real successful run; before execution they
are not claimed to exist. No arbitrary sleep substitutes for UI assertions.
The bounded startup poll waits for actual DEMO_MODE configuration.

## Local evidence

`bash .uak/bin/q uv run pytest -q tests/e2e` returned
`OK exit=0 30s · ... [100%]` on 2026-10-10: all three initial cases passed.
After independent review strengthened the separate ACTIVE/approval gates and
the per-business share checks, the final Verify with `PYTHONUTF8=1` returned
`OK exit=0 38s · ... [100%]` (all three cases passed).
The first run hit the 30-second cold-start deadline; the startup poll now allows
90 seconds and emits unbuffered server logs. The next run exposed Windows
TIME_WAIT in the bind-based preflight; the preflight now checks for a listening
server. Neither fix changes app behavior or supplies a test response.

Actual final-state captures:
[desktop 1280×720](artifacts/checkout-1280x720.png) and
[mobile 390×844](artifacts/checkout-390x844.png).

Clean CI preparation is pending the owner of HACK-001 (request #362): the
current smoke adapter runs pytest before npm ci and CI does not install
Chromium. The app-owned CI/smoke files were not edited by HACK-019. Until that
order is fixed, local success with explicit preparation is not clean CI proof.

The first product smoke returned exit 1 in 391 seconds: secret scan and Ruff
passed, pytest reported 107 passed / 2 failed. Both failures were in
`app/tests/test_pharmacy_fixture.py` (lines 59 and 126), where the default Windows
text decoding changed accented fixture strings. No pharmacy files were edited;
the rerun uses the explicit `PYTHONUTF8=1` condition.
