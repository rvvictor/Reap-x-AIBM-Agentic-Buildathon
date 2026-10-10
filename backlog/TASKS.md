# Backlog published on claims (uak plan)

Append-only; added to .uak/TASKS.md from main. Why: adding tasks never waits for a PR.
## HACK-013 · Fixtures de una farmacia para demostrar generalización

- **Type:** feature
- **Priority:** P1
- **Estimate:** 25 min
- **Rubric / Spec:** Originalidad · IDEA.md
- **Depends on:** None
- **Uses contract:** HACK-002
- **Related:** HACK-004
- **Paths:** app/fixtures/pharmacy/, app/tests/test_pharmacy_fixture.py
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Fixture de una farmacia con 10 productos (paracetamol, antigripal, claritromicina, antiácido...) y ventas sintéticas con pico de frío, todo `demo_data: true`
  - El mismo motor de predicción corre sobre este negocio sin cambios de código
  - Escenario: base 10 sube a 20 en antigripales y baja a 5 en dolor de estómago
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_pharmacy_fixture.py`
- **Next step:** Generar el fixture con la misma forma que el de cafeterías

## HACK-014 · Backtest: predicción dinámica vs stock fijo

- **Type:** feature
- **Priority:** P1
- **Estimate:** 30 min
- **Rubric / Spec:** Ejecución técnica · IDEA.md
- **Depends on:** None
- **Uses contract:** HACK-002
- **Related:** HACK-004
- **Paths:** app/services/backtest.py, app/routers/backtest.py, app/tests/test_backtest.py
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Compara ventas perdidas y sobrante entre stock fijo y objetivo dinámico sobre el historial simulado
  - El resultado se etiqueta como simulado y muestra la fórmula usada
  - `GET /api/backtest/{business_id}`
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_backtest.py`
- **Next step:** Implementar la simulación día a día con el motor de HACK-004

## HACK-015 · Capa de confianza: reglas de autorización y bitácora de auditoría

- **Type:** feature
- **Priority:** P0
- **Estimate:** 30 min
- **Rubric / Spec:** Confianza y control · IDEA.md
- **Depends on:** None
- **Uses contract:** HACK-002
- **Related:** HACK-006, HACK-008
- **Paths:** app/services/policy.py, app/routers/policy.py, app/tests/test_policy.py
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Reglas verificables: tope de presupuesto, sustituciones permitidas, cantidad máxima y detención si el precio cambia fuera de lo autorizado
  - Cada decisión del agente queda en una bitácora con motivo, hora y quién autorizó
  - `GET /api/audit` devuelve la bitácora
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_policy.py`
- **Next step:** Implementar las reglas como funciones puras con pruebas

## HACK-016 · UI: configuración del negocio (stock base, límites, presupuesto)

- **Type:** feature
- **Priority:** P1
- **Estimate:** 30 min
- **Rubric / Spec:** Problema que vale la pena · IDEA.md
- **Depends on:** HACK-001
- **Uses contract:** HACK-002
- **Related:** HACK-009
- **Paths:** web/src/features/settings/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - El dueño edita stock base, mínimo, máximo y presupuesto por producto
  - Estados vacío, cargando y error; se ve a 1280×720 y a 390×844
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `npm --prefix web run build`
- **Next step:** Crear el formulario con datos mock del contrato

## HACK-017 · UI: pedidos, entregas y ahorro acumulado

- **Type:** feature
- **Priority:** P1
- **Estimate:** 30 min
- **Rubric / Spec:** Potencial comercial · IDEA.md
- **Depends on:** HACK-001
- **Uses contract:** HACK-002, HACK-008
- **Related:** HACK-010
- **Paths:** web/src/features/orders/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Lista de pedidos con estado real por negocio y ahorro acumulado vs precio a vencer
  - Cada número tiene fuente o etiqueta `demo_data`
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `npm --prefix web run build`
- **Next step:** Crear la pantalla con datos mock

## HACK-018 · Guion de pitch y video de 1-2 minutos

- **Type:** docs
- **Priority:** P0
- **Estimate:** 25 min
- **Rubric / Spec:** Todos · IDEA.md
- **Depends on:** None
- **Uses contract:** HACK-011
- **Related:** None
- **Paths:** docs/PITCH.md, docs/VIDEO.md
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Pitch de 3 minutos: problema, wow de predicción, wow de ahorro en grupo, confianza y control
  - Guion del video de 1 a 2 minutos con tomas y tiempos
  - Plan B si falla la red
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `test -s docs/PITCH.md`
- **Next step:** Redactar el pitch desde IDEA.md

## HACK-019 · Pruebas E2E del flujo con Playwright y DEMO_MODE

- **Type:** demo
- **Priority:** P1
- **Estimate:** 30 min
- **Rubric / Spec:** Ejecución técnica · IDEA.md
- **Depends on:** HACK-001
- **Uses contract:** HACK-009, HACK-010
- **Related:** None
- **Paths:** tests/e2e/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Prueba E2E del flujo de 6 pasos con movimiento reducido, esperando el estado final
  - Captura de pantalla a 1280×720 y a 390×844
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q tests/e2e`
- **Next step:** Escribir la prueba del paso 1 al 4
