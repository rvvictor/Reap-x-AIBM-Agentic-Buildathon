# IDEA · Bodega

> Challenge: Reap x AIBM Agentic Buildathon · Event: Reap x AI Builders Mexico, 2026-10-09 17:00-21:00 CDMX. Tags: **[Decided]** · **[Recommended]** · **[To validate]**.
> Every pitch number comes from §10 with a source. §4 → vertical tasks · §6 → contract · §7 → spikes · §8 → acceptance.
> Idea completa y generalizada: `docs/IDEA-GENERAL.md`.

## 0. Name and brand (fixed at T0)
- Name: **Bodega** · repo/domain: Reap-x-AIBM-Agentic-Buildathon · tagline: TBD (8 palabras o menos).
- Renaming after T−50% needs a human `uak decision`. El nombre debe fijarse antes de `/uak-design-lock`.

## 1. One line
For **dueños de negocios pequeños sin contrato con distribuidores**, who **fijan un stock estático y pierden ventas o inmovilizan capital**, **Bodega** lets them **tener un stock objetivo dinámico por producto y comprar en grupo más barato** , unlike **reponer a ojo y pedir cada quien por su cuenta**. [Decided]
Edge over other teams: la mayoría hará chatbots de compra o agentes de pedido; nosotros ponemos la **predicción de stock por producto** como núcleo y un agente global que agrupa y compara proveedores. [To validate]

## 2. Users
| Persona | Moment | Need | Flow step |
|---|---|---|---|
| Dueña de cafetería (demo) | Se acerca el frío y su stock fijo no alcanza | Saber cuánto de cada producto pedir | 2 |
| Dueño de negocio (cualquier giro) | Revisa qué le falta esta semana | Comprar más barato sin cambiar de proveedor a la fuerza | 4, 5 |
| Operador/jurado | Quiere ver el ahorro y el control | Ver quién gana cuánto y quién autorizó | 4, 5 |

## 3. Demo case
Cuatro cafeterías de una zona (datos simulados, `demo_data: true`) con historial de ventas de granos, filtros y vasos. Llega temporada de frío y hay un evento cercano: el agente local de cada una sube o baja el objetivo de **cada producto** y detecta faltas. La farmacia (paracetamol 10→20, antigripal 10→15, dolor de estómago 10→5) se presenta como ejemplo de generalización en el pitch. Elegida porque Coffee & Tea es la categoría con más comercios soportados por Reap (17 en el PDF de merchants). [Decided]

## 4. Demo flow (6 steps or fewer, 3 min or less; each step = one vertical task)
| # | User does | Sees on screen | API | Prio |
|---|---|---|---|---|
| 1 | Elige su negocio y ve su stock base y actual | Tabla de productos con base, actual, última actualización y etiqueta `demo_data` | `GET /api/businesses/{id}/inventory` | P0 |
| 2 | Pulsa "Predecir stock" | **Wow 1:** objetivo dinámico por producto (base → nuevo), motivos (temporada, historial, evento) y confianza | `POST /api/businesses/{id}/forecast` | P0 |
| 3 | Pulsa "Detectar faltas" en los 4 negocios | Faltas por producto publicadas al agente global, agrupadas por categoría | `POST /api/needs/publish` | P0 |
| 4 | Abre la vista del agente global | **Wow 2:** comparación de proveedores por categoría, costo total entregado y ahorro por negocio vs su "precio a vencer" | `POST /api/global/proposals` | P0 |
| 5 | Cada dueño autoriza su parte (tope de presupuesto) y se paga | Aprobación en la página de Reap sandbox, orden confirmada, reparto por negocio | `POST /api/global/proposals/{id}/approve` | P0 |
| 6 | Se agota un producto / vence la cotización | El agente recalcula dentro de lo autorizado o se detiene y pide aprobación | `POST /api/global/proposals/{id}/recheck` | P1 |

- Wow in one sentence: "El agente sabe cuánto stock necesita cada producto y consigue que cuatro negocios paguen menos juntos que solos." · seconds until the wow: 45 or fewer. Plan B for steps that need network: respuestas grabadas de Reap y video preparado (`DEMO_MODE`). [Decided]

## 5. Technical core
- Method: stock objetivo = demanda esperada (EWMA de velocidad de venta × factor de temporada × factor de evento) × tiempo de entrega + colchón de seguridad, acotado por mínimo/máximo del dueño, capacidad y presupuesto. Cálculo determinista y probado. [Decided]
- The LLM does **not** produce the key number: el LLM convierte eventos/clima en señales estructuradas (categorías afectadas, dirección, magnitud acotada, fuente) validadas contra un esquema, y redacta las explicaciones. El cálculo de objetivos, ahorro y reparto es código. [Decided]
- Agente global: agrupa por categoría/producto equivalente, compara costo total entregado entre proveedores y calcula el ahorro por negocio. El reparto debe beneficiar a cada negocio; si alguno sale peor, se excluye o se recalcula. [Decided]
- Honest validation: backtest de la predicción contra historial simulado (error vs stock fijo, ventas perdidas evitadas), reportado como simulado. No hay dataset público elegido todavía. [To validate]

## 6. Data (contract in `app/schemas/`)
| Entity | Key fields | Source (license) |
|---|---|---|
| Business | id, name, vertical, location, budget_cap, allowed_substitutions | simulated (`demo_data`) |
| Product (SKU) | id, business_id, name, category, unit, base_stock, min, max, current_stock, updated_at | simulated |
| SalesRecord | sku_id, date, qty | simulated |
| Signal | id, kind (season/event/weather), categories, direction, magnitude, source, valid_from/to | LLM + schema, with cited source |
| Forecast | sku_id, base, target, reasons[], confidence | computed |
| Need | business_id, sku_id, qty, needed_by, accepted_equivalents | computed |
| SupplierOffer | supplier, product_id, variant_id, unit_price, shipping, tax, currency, eta | Reap search/quote (sandbox) or simulated tiers (`demo_data`) |
| Proposal / Allocation | id, group, total, savings_per_business, status | computed |

## 7. AI and external APIs (each = a 30-min spike + a recorded fallback)
| Use | Model/API [To validate] | Key owner | Fallback |
|---|---|---|---|
| Búsqueda, cotización y checkout | Reap Agentic API (`https://sandbox.api.reap.global`: `/agentic/products/search`, `/quotes`, `/checkouts`, enrollments EXTERNAL) | Fernando Vargas | Respuestas grabadas + `X-Simulate-Checkout: COMPLETED` |
| Valor de `Reap-Version` y headers | docs.reap.global API Reference / Telegram | Fernando Vargas | Preguntar en Telegram al inicio |
| Señales desde eventos y clima | Claude (modelo fijado en un solo archivo de config) | Un humano del equipo | Señales de ejemplo grabadas en JSON |
| MCP (agentes local↔global) | Servidor MCP propio con herramientas `publicar_faltas`, `consultar_ofertas`, `proponer_compra` | Un humano del equipo | Llamadas HTTP directas entre servicios |
| Precio por volumen | **No verificado** en Reap | — | Escalas de precio simuladas y etiquetadas `demo_data` |

## 8. Rubric → evidence
Rúbrica oficial no publicada (unverified). Criterios que Codex encontró en la convocatoria de Luma (sin verificar): ejecución técnica, originalidad, potencial comercial, mecanismos de confianza y control.
| Official criterion | Weight | Step/artifact that proves it |
|---|---|---|
| Track 1: Most Worthwhile Problem | n/d | Pasos 1-4 (problema real, ahorro por negocio) |
| Agentic module central | gate | Pasos 4-5 (búsqueda, cotización y checkout en sandbox) |
| Confianza y control | n/d | Paso 5-6 (autorización por negocio, el agente se detiene) |
| Ejecución técnica | n/d | Predicción con motivos + compra de punta a punta |

## 9. Scope
Out: negocios con contratos recurrentes con distribuidores, logística propia, cobros recurrentes (mandates no disponibles), compras reales, perecederos complejos, viajes y categorías restringidas · Simulated with `demo_data`: historiales, inventarios, 4 negocios, escalas de precio si Reap no las da · UI language: español, con términos de producto en inglés donde aplique · Ethics/data: sandbox únicamente, sin tarjetas reales, el agente nunca ve datos de tarjeta, sin scraping del checkout.

## 10. Citable facts (verified on 2026-10-09)
| Fact | Source URL |
|---|---|
| Todo proyecto debe usar el Agentic module de Reap (o el wallet module con Agentic) | https://aibuilders.mx/reap |
| Sandbox único, sin dinero real; solo comercios soportados | https://aibuilders.mx/reap |
| Base sandbox `https://sandbox.api.reap.global`; headers Authorization, Reap-Version, Idempotency-Key | https://docs.reap.global/agentic-payments/setup |
| Flujo: enrollment → search → quote → checkout → confirmar orden; mandates no disponibles | https://docs.reap.global/agentic-payments/overview |
| Header `X-Simulate-Checkout: COMPLETED` solo en sandbox | https://docs.reap.global/agentic-payments/one-time-purchases |
| ~152 comercios soportados (US 64, SG 48, MX 3); Coffee & Tea 17 | `Reap - List of Supported Merchant.pdf` (local, no versionado) |
| Cifras de ahorro de la demo | **simuladas, sin fuente** (`demo_data: true`) |
