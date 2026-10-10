# TASKS · stateless backlog

State lives on the `claims` branch (`uak status`); this file holds only tasks.

## HACK-001 · Esqueleto FastAPI + React corriendo con DEMO_MODE

- **Type:** setup
- **Priority:** P0
- **Estimate:** 20 min
- **Rubric / Spec:** Todos · IDEA.md
- **Depends on:** None
- **Uses contract:** None
- **Related:** None
- **Paths:** pyproject.toml, uv.lock, package.json, package-lock.json, web/package.json, web/package-lock.json, app/main.py, app/config.py, app/__init__.py, app/routers/__init__.py, app/services/__init__.py, web/src/App.tsx, web/src/index.css, web/src/main.tsx, web/src/vite-env.d.ts, web/tsconfig.app.json, web/tsconfig.node.json, web/public/, web/.gitignore, web/eslint.config.js, app/tests/test_health.py, .python-version, .uak/bin/smoke-project, web/src/lib/api.ts, web/index.html, web/vite.config.ts, web/tsconfig.json, .env.example, .gitignore, .github/workflows/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Sigue `.uak/stacks/fastapi-react/STACK.md`; `app/main.py` autodescubre routers y sirve `web/dist`
  - `GET /api/health` responde 200; `npm run build` en `web/` pasa
  - `app/config.py` fija el ID de modelo en un solo lugar y define `DEMO_MODE` y `REAP_*` desde `.env` (nunca claves en git)
  - `.env.example` sin secretos
  - El test de salud va en `app/tests/test_health.py` (STACK.md lo escribe por error en `app/.uak/tests/`); genera el smoke con `bash .uak/bin/uak init-smoke --command "<Product smoke de STACK.md>"`
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_health.py`
- **Next step:** Ejecutar los pasos de setup de STACK.md

## HACK-002 · Contrato de datos, fixtures de 4 cafeterías y DESIGN.md provisional

- **Type:** contract
- **Priority:** P0
- **Estimate:** 25 min
- **Rubric / Spec:** Todos · IDEA.md
- **Depends on:** None
- **Uses contract:** None
- **Related:** None
- **Paths:** app/schemas/, app/fixtures/businesses/, web/DESIGN.md, app/tests/test_schemas.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Esquemas pydantic: Business, Product, SalesRecord, Signal, Forecast, Need, SupplierOffer, Proposal, Allocation (ver IDEA.md §6)
  - Fixtures JSON (en app/fixtures/businesses/) con 4 negocios y ~90 días de ventas sintéticas con estacionalidad, cada registro con `demo_data: true`
  - `web/DESIGN.md` con una dirección visual y tokens de color
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_schemas.py`
- **Next step:** Crear app/schemas/ y publicar con `uak msg related:HACK-002 --kind contract`

## HACK-003 · Spike Reap: cliente sandbox y respuestas grabadas

- **Type:** spike
- **Priority:** P0
- **Estimate:** 30 min
- **Rubric / Spec:** Todos · IDEA.md
- **Depends on:** None
- **Uses contract:** HACK-002
- **Related:** None
- **Paths:** app/integrations/reap/, app/fixtures/reap/, app/tests/test_reap_client.py, docs/REAP-NOTES.md
- **Freeze-Allowed:** no
- **Acceptance:**
  - Cliente httpx con Authorization, Reap-Version, Idempotency-Key; clave solo desde `.env`
  - Búsqueda de café (`Coffee & Tea`), cotización y checkout con `X-Simulate-Checkout: COMPLETED` probados en sandbox, o dejados documentados como bloqueados con el error exacto
  - Respuestas reales guardadas en `app/fixtures/reap/` y usadas cuando `DEMO_MODE=true`
  - Se confirma el valor de `Reap-Version` y se anota en `docs/REAP-NOTES.md`
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_reap_client.py`
- **Next step:** Pedir a Fernando la clave en su `.env` local y el valor de Reap-Version

## HACK-004 · Motor de predicción de stock por producto

- **Type:** feature
- **Priority:** P0
- **Estimate:** 30 min
- **Rubric / Spec:** Ejecución técnica · IDEA.md
- **Depends on:** None
- **Uses contract:** HACK-002
- **Related:** None
- **Paths:** app/services/forecast.py, app/routers/forecast.py, app/tests/test_forecast.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Dado un producto con base 10 y señal de frío, el objetivo dinámico sube; con señal inversa baja; siempre acotado por min/max
  - Devuelve `reasons[]` y `confidence`; mismo input produce mismo output
  - Funciona con fixtures y señales grabadas; `POST /api/businesses/{id}/forecast`
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_forecast.py`
- **Next step:** Implementar demanda = EWMA × temporada × evento + colchón

## HACK-005 · Señales: eventos/clima a señales estructuradas con LLM

- **Type:** feature
- **Priority:** P0
- **Estimate:** 30 min
- **Rubric / Spec:** Originalidad · IDEA.md
- **Depends on:** None
- **Uses contract:** HACK-002
- **Related:** None
- **Paths:** app/services/signals.py, app/routers/signals.py, app/fixtures/signals/, app/tests/test_signals.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - El LLM (modelo fijado en config) devuelve JSON validado contra el esquema Signal; salida inválida se rechaza
  - Con `DEMO_MODE=true` usa señales grabadas, sin llamar a ningún modelo
  - Cada señal cita su fuente; magnitud acotada
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_signals.py`
- **Next step:** Definir el prompt y el validador de esquema

## HACK-006 · Agente global: agrupar faltas, comparar proveedores y repartir ahorro

- **Type:** feature
- **Priority:** P0
- **Estimate:** 30 min
- **Rubric / Spec:** Ejecución técnica · Originalidad · IDEA.md
- **Depends on:** None
- **Uses contract:** HACK-002, HACK-003
- **Related:** None
- **Paths:** app/services/global_agent.py, app/routers/global_agent.py, app/tests/test_global_agent.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Agrupa Need de varios negocios por categoría y producto equivalente
  - Compara SupplierOffer por costo total entregado y calcula ahorro por negocio vs su precio a vencer
  - Si un negocio sale peor, se excluye y se recalcula; escalas de precio simuladas llevan `demo_data: true`
  - `POST /api/global/proposals`
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_global_agent.py`
- **Next step:** Implementar agrupación y reparto con datos de fixtures

## HACK-007 · Servidor MCP entre agente local y global

- **Type:** feature
- **Priority:** P1
- **Estimate:** 30 min
- **Rubric / Spec:** Originalidad · IDEA.md
- **Depends on:** None
- **Uses contract:** HACK-002
- **Related:** HACK-004, HACK-006
- **Paths:** app/mcp/, app/tests/test_mcp.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Herramientas `publicar_faltas`, `consultar_ofertas`, `proponer_compra` expuestas por MCP
  - El agente local publica una falta y el global la recibe en una prueba
  - Si el tiempo no alcanza, queda documentado el fallback a HTTP directo
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_mcp.py`
- **Next step:** Esqueleto del servidor MCP con las 3 herramientas

## HACK-008 · Pagos: enrollment, checkout y aprobación por negocio

- **Type:** integration
- **Priority:** P0
- **Estimate:** 30 min
- **Rubric / Spec:** Agentic module central · Confianza y control · IDEA.md
- **Depends on:** HACK-003
- **Uses contract:** HACK-002, HACK-006
- **Related:** None
- **Paths:** app/routers/payments.py, app/services/payments.py, web/src/features/checkout/, app/tests/test_payments.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Enrollment EXTERNAL con returnUrl HTTPS y confirmación `ACTIVE` antes de cobrar
  - Cada negocio autoriza su parte con tope de presupuesto; sin autorización no hay checkout
  - Tras el checkout se lee el pedido y se concilia contra `finalAmount`; cotización vencida o cambio fuera de lo autorizado detiene y pide aprobación
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `uv run pytest -q app/tests/test_payments.py`
- **Next step:** Implementar el reparto interno y llamar al cliente de HACK-003

## HACK-009 · UI del negocio: inventario y predicción por producto

- **Type:** feature
- **Priority:** P0
- **Estimate:** 35 min
- **Rubric / Spec:** Problema que vale la pena · IDEA.md
- **Depends on:** HACK-001
- **Uses contract:** HACK-002, HACK-004
- **Related:** None
- **Paths:** web/src/features/business/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Muestra base, actual, objetivo dinámico, motivos y confianza por producto, con etiqueta `demo_data`
  - Estados vacío, cargando y error; legible a 1280×720 sin scroll
  - Se ve usable a 390×844
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `npm --prefix web run build`
- **Next step:** Crear la pantalla con datos mock del contrato

## HACK-010 · UI del agente global: comparación, ahorro y aprobación

- **Type:** feature
- **Priority:** P0
- **Estimate:** 35 min
- **Rubric / Spec:** Problema que vale la pena · Confianza y control · IDEA.md
- **Depends on:** HACK-001
- **Uses contract:** HACK-002, HACK-006, HACK-008
- **Related:** None
- **Paths:** web/src/features/global/
- **Freeze-Allowed:** no
- **Acceptance:**
  - Muestra comparación de proveedores por categoría, costo total entregado y ahorro por negocio
  - Botón de autorización por negocio y estado real de cada pedido
  - El wow se ve en 45 s a 1280×720; cada número tiene fuente o etiqueta `demo_data`
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `npm --prefix web run build`
- **Next step:** Crear la pantalla con datos mock de la propuesta

## HACK-011 · Demo: flujo completo en DEMO_MODE, README y guion de video plan B

- **Type:** demo
- **Priority:** P0
- **Estimate:** 30 min
- **Rubric / Spec:** Todos · IDEA.md
- **Depends on:** HACK-001
- **Uses contract:** HACK-004, HACK-006, HACK-008, HACK-009, HACK-010
- **Related:** None
- **Paths:** README.md, docs/DEMO.md, e2e/
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Con `DEMO_MODE=true` el flujo de 6 pasos corre sin claves ni red
  - README en inglés con capturas reales, `.env.example` y cómo correr el demo
  - Guion del video de 1-2 min en `docs/DEMO.md`
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `bash .uak/bin/smoke`
- **Next step:** Probar el flujo completo y grabar el video plan B

## HACK-012 · Entrega en Gavel: descripción, enlaces y checklist

- **Type:** docs
- **Priority:** P0
- **Estimate:** 20 min
- **Rubric / Spec:** Todos · IDEA.md
- **Depends on:** None
- **Uses contract:** HACK-011
- **Related:** None
- **Paths:** docs/SUBMISSION.md
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Descripción del proyecto de 5000 caracteres o menos, con tracks elegidos (máx. 2)
  - Checklist de los 9 puntos del evento marcado
  - Enlace del repo, video y miembros listos para pegar; el envío lo hace Fernando Vargas
  - `bash .uak/bin/smoke` exits 0
- **Verify:** `test -s docs/SUBMISSION.md`
- **Next step:** Redactar docs/SUBMISSION.md desde IDEA.md
