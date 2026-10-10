# worklog/WL-1791597278-sebastian-2-HACK-004-hack.ae0InN.md · HACK-004

## Live summary
- Done: Claim created; implementation pending
- Decision: Own branch and worktree
- Why: Parallel work without touching the main checkout
- Failing: No validation run yet
- Commands: `uv run pytest -q app/tests/test_forecast.py`
- Next: Implementar demanda = EWMA × temporada × evento + colchón

## History
- 1791597278 | CLAIMED | sebastian-2 | claim; next: Implementar demanda = EWMA × temporada × evento + colchón
- 1791597330 | CLAIMED | sebastian-2 | pending decision HACK-004-1791597330; option: Stack local HACK-001 para pruebas; adapter provisional IDEA.md sin tocar schemas ni fixtures ajenos; Why: Esqueleto en REVIEW y contrato HACK-002 pendiente; permite verificar motor independiente
