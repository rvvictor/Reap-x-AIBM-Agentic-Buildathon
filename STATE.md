# STATE

Phase: execution
Updated: 1791598722
AVAILABLE: HACK-007 HACK-008 HACK-011 HACK-012 HACK-013 HACK-014 HACK-015 HACK-016 HACK-017 HACK-018 HACK-019 
CLAIMED: HACK-004 HACK-006 HACK-009 HACK-010 
BLOCKED: -
REVIEW: HACK-003 HACK-005 
INTEGRATED: HACK-001 HACK-002 
CANCELLED: -

Claims (first 24; status --task ID shows detail):
HACK-003 | REVIEW | fernando-1 | until 1791612988
HACK-004 | CLAIMED | sebastian-2 | until 1791599978
HACK-005 | REVIEW | dylan-1 | until 1791613046
HACK-006 | CLAIMED | sebastian-1 | until 1791601247
HACK-009 | CLAIMED | victor-1 | until 1791600135
HACK-010 | CLAIMED | dylan-2 | until 1791601422

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1791598249 | deadline decision/HACK-004-1791597330/1791598230 | REVERSIBLE_AND_LOG | Option: Stack local HACK-001 para pruebas; adapter provisional IDEA.md sin tocar schemas ni f
- 1791598368 | HACK-005 | Preserve human merge queue; do not bypass automatic scope gate | Why: Gate includes HACK001 upstream files from original Task-Base; current-main diff has 
- 1791598547 | HACK-006 | Canonical contracts; MXN landed baselines; known-unit equivalence; business-level exclusion; caller quotes demo-only | Why: Apply advisor invariants; draf
- 1791598498 | HACK-003 | sandbox sigue bloqueado sin REAP_API_KEY; el criterio queda cubierto con el 401 grabado | Why: no hay clave en .env
- 1791598722 | HACK-010 | Draft pending actual backend integration and real payment contract | Why: HACK006 not published; HACK008 AVAILABLE; request/response conflicting messages1

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
