# worklog/WL-1791597070-fernando-1-HACK-003-hack.Tdr97e.md · HACK-003

## Live summary
- Done: cliente httpx, fixtures 401, pytest 5 passed
- Decision: sin clave no hay checkout COMPLETED; DEMO_MODE lee las respuestas grabadas
- Why: no hay .env ni REAP_API_KEY
- Failing: smoke exit 2: missing .uak/bin/smoke-project (HACK-001)
- Commands: uv run pytest -q app/tests/test_reap_client.py
- Next: Poner REAP_API_KEY en .env del worktree y repetir search/quote/checkout; smoke cuando HACK-001 esté en main

## History
- 1791597070 | CLAIMED | fernando-1 | claim; next: Pedir a Fernando la clave en su .env local y el valor de Reap-Version
- 1791597248 | CLAIMED | fernando-1 | heartbeat; lease until 1791599948
- 1791597348 | CLAIMED | fernando-1 | heartbeat; lease until 1791600048
- 1791597730 | CLAIMED | fernando-1 | heartbeat; lease until 1791600430
- 1791597794 | CLAIMED | fernando-1 | checkpoint; next: Poner REAP_API_KEY en .env del worktree y repetir search/quote/checkout; smoke cuando HACK-001 esté en main
