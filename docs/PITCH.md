# Bodega · pitch de 3 minutos

Guion hablado en español, con pausas para señalar la pantalla. Objetivo: 3:00; ensayar con cronómetro antes de presentarlo. El video corto y las instrucciones de grabación están en [VIDEO.md](VIDEO.md).

## 0:00–0:25 · Problema

«Una cafetería pequeña compra sola y decide cuánto reponer mirando lo que compró la semana pasada. Si cambia la demanda, puede quedarse sin producto o dejar dinero inmovilizado en inventario. El problema tiene dos decisiones: cuánto necesito comprar y cuánto me cuesta conseguirlo. Bodega conecta esas decisiones para negocios pequeños sin contrato con distribuidores.»

## 0:25–0:55 · Wow 1: objetivo por producto

**Pantalla:** tabla “Café Aurora · inventario y predicción”; señalar base, actual, objetivo y motivos. El primer wow aparece antes del segundo 45.

«Aquí vemos un ejemplo simulado: el café pasa de una base de doce bolsas a un objetivo de dieciséis; otro producto puede bajar. Cada producto tiene motivos visibles. Esta tabla ilustra la predicción con datos de ejemplo. El motor del backend calcula objetivos con historial, señales, tiempo de entrega y un colchón, respetando límites y presupuesto. La confianza mostrada es una heurística, no una garantía de ventas.»

## 0:55–1:20 · De la falta al agente global

«El LLM puede transformar clima o eventos en señales estructuradas, pero no decide el número final: ese cálculo es determinista. En esta demo las señales también son simuladas. Cuando falta stock, el agente local puede publicar necesidades mediante MCP. El agente global agrupa productos equivalentes y compara ofertas. Hoy mostramos esos componentes con ejemplos; la tabla del negocio todavía no alimenta automáticamente la compra.»

## 1:20–1:55 · Wow 2: ahorro por negocio

**Pantalla:** `#global`, selector **Datos → Demo**; costo entregado y reparto visibles.

«Cuatro cafeterías juntan veinte bolsas. En esta comparación simulada, comprar por separado cuesta cinco mil ochocientos noventa y dos pesos; juntas, cuatro mil quinientos veinticuatro, incluyendo envío e IVA. La diferencia es mil trescientos sesenta y ocho pesos para el grupo. Podemos ver cuánto corresponde a cada negocio. Son cifras del fixture de demostración, no descuentos obtenidos de Reap ni ahorro medido en comercios reales. El servicio descarta participantes que no se benefician.»

## 1:55–2:35 · Confianza y control

**Pantalla:** **Datos → API con datos de ejemplo**, **Recalcular propuesta**, autorizaciones y estado del pedido. Esta vista usa otro precio individual de referencia; no repetir los montos de la vista Demo.

«En el modo API, el servidor calcula una propuesta con ofertas de ejemplo. Cada negocio autoriza su parte con su tope de presupuesto. El estado de autorización y del pedido vuelve del servidor. Un monto distinto o una orden vencida obliga a pedir nueva aprobación; no se recalcula ni se cobra automáticamente. El checkout que enseñamos es simulado, sin dinero real. La integración con Reap existe, pero no hemos verificado un checkout completado en su sandbox.»

## 2:35–3:00 · Cierre

«Bodega reúne predicción por producto, ahorro compartido y control individual. Hoy demostramos cálculos y autorizaciones con datos simulados. El siguiente paso es validar con negocios reales, conectar toda la experiencia y completar la prueba del sandbox. Bodega ayuda a decidir mejor y comprar juntos.»

## Evidencia y límites para preguntas

| Afirmación | Fuente del repositorio / alcance |
|---|---|
| Problema y propuesta de valor | [IDEA.md](../IDEA.md), §§1–5; hipótesis de producto, sin entrevistas ni validación comercial reportadas. |
| Base 12 → objetivo 16 | [business/index.tsx](../web/src/features/business/index.tsx), `MOCK`; ilustración fija, no resultado de una llamada al forecast desde esa pantalla. |
| Motor determinista y límites | [forecast.py](../app/services/forecast.py); no afirmar un backtest, precisión medida ni reducción de ventas perdidas. |
| Herramientas MCP | [app/mcp/README.md](../app/mcp/README.md); coordinador de confianza en demo, no autorización de producción. |
| 20 bolsas; $5,892 → $4,524; ahorro $1,368 MXN | [global/data.ts](../web/src/features/global/data.ts), `sampleProposal`: `20×190+100+624=4524`; `5892−4524=1368`; por negocio `1473−1131=342`. Solo vista Demo. |
| API, autorización y conciliación | [global/payments.tsx](../web/src/features/global/payments.tsx), [payments.py](../app/services/payments.py); `DEMO_MODE`, sin autenticación de titulares en producción. |
| Sandbox externo pendiente | [REAP-NOTES.md](REAP-NOTES.md); no presentar errores grabados de autenticación como cotizaciones exitosas. |

Si falla la red, usar el modo demo local ya preparado. Si falla la app, reproducir el video **previamente grabado y comprobado**, o las capturas verificadas; anunciar el cambio. El plan B detallado está en [VIDEO.md](VIDEO.md#plan-b).
