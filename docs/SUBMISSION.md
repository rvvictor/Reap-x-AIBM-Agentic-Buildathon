# Entrega en Gavel · Bodega

Envío: https://gavel-65labs.vercel.app/submit/74oz5tv1cfzllzh392gy1rqzvx4m1vop
**Quién envía: Fernando Vargas (capitán).** Plazo oficial: 2026-10-09 23:59 CDMX · envío interno: 23:39.

## Campos del formulario (copiar y pegar)
| Campo | Valor |
|---|---|
| Team name | Axolutions |
| Team captain | Fernando Vargas |
| Contact email | vargas.fer2442@gmail.com |
| Project link | https://github.com/rvvictor/Reap-x-AIBM-Agentic-Buildathon |
| Demo video link | https://drive.google.com/drive/folders/1gcftspbgiJxqikfsjdwF6HRyvDFx5eGi?usp=sharing (carpeta de Drive con el video de 1:45; plan B local `docs/demo-planb.mp4`) |
| Team members | Fernando Vargas, Victor Ruiz, Sebastian Jara, Javier Reyna, Dylan Martinez |
| Sponsor prize tracks (máx. 2) | Reap Most Worthwhile Problem |

El track "Reap Best Bridge Onchain-Real World" **no** se elige: el equipo confirmó que aplica solo al Track 1.

## Descripción del proyecto (límite 5000 caracteres)
**Bodega: stock objetivo dinámico por producto y compras en grupo más baratas para negocios pequeños.**

Los dueños de negocios pequeños, sin contrato con distribuidores, fijan un stock estático: cuando cambia la temporada o hay un evento cercano pierden ventas por faltantes o inmovilizan capital en exceso. Además piden cada quien por su cuenta y pagan el precio más alto.

Bodega pone un agente local en cada negocio y un agente global que los coordina.

1. **Predicción por producto.** El agente local calcula un stock objetivo para cada producto: demanda esperada (promedio móvil exponencial de la velocidad de venta) × factor de temporada × factor de evento, por el tiempo de entrega, más un colchón de seguridad, acotado por el mínimo y máximo del dueño. El cálculo es determinista y está probado. Cada objetivo muestra su base, el nuevo valor, los motivos y la confianza.
2. **El LLM no produce el número clave.** Claude convierte eventos y clima en señales estructuradas (categorías afectadas, dirección, magnitud acotada y fuente), validadas contra un esquema, y redacta las explicaciones. Los objetivos, el ahorro y el reparto son código.
3. **Agente global.** Recibe las faltas de varios negocios, las agrupa por categoría, compara proveedores por costo total entregado y reparte el ahorro. Si algún negocio saliera peor que comprando solo, se excluye o se recalcula.
4. **Compra con control.** Búsqueda, cotización y checkout usan el Agentic module de Reap en sandbox. Cada dueño autoriza su parte dentro de su tope de presupuesto; si se agota un producto o vence la cotización, el agente recalcula dentro de lo autorizado o se detiene y pide aprobación. El agente nunca ve datos de tarjeta.

**Demo.** Cuatro cafeterías de una zona con historial de ventas de granos, filtros y vasos. Llega el frío y hay un evento cercano: el agente de cada cafetería sube o baja el objetivo de cada producto, detecta faltas y las publica; el agente global compara proveedores y muestra cuánto ahorra cada negocio frente a su precio actual. La idea generaliza a otros giros, por ejemplo una farmacia.

**Honestidad sobre los datos.** Inventarios, historiales de ventas, los 4 negocios y las cifras de ahorro de la demo son **simulados** y están etiquetados `demo_data: true`. Todo el flujo con Reap ocurre en el sandbox, sin dinero real. Si Reap no ofrece escalas de precio por volumen, usamos escalas simuladas y etiquetadas. La validación de la predicción es un backtest contra historial simulado y se reporta como tal. Con `DEMO_MODE` el flujo corre sin claves ni red, con respuestas grabadas de Reap.

**Stack.** FastAPI + React, servidor MCP entre agente local y global, Reap Agentic API, Claude para señales.

## Checklist de entrega
Los 9 puntos oficiales de https://aibuilders.mx/reap, más los pasos de envío. `[x]` = con evidencia o confirmado por el equipo; `[ ]` = falta confirmar.

- [x] 1. Mi proyecto usa el Agentic module, con Reap API o con el wallet module (Reap Agentic API: `app/integrations/reap/`)
- [x] 2. Los pagos agénticos son el centro del producto, no un extra (reparto de ahorro, autorización por negocio y checkout)
- [x] 3. Todo corre en sandbox y no se mueve dinero real (README: solo sandbox; `DEMO_MODE` sin red)
- [ ] 4. Solo uso merchants de la lista soportada (/merchants en el bot de Telegram): el proyecto parte del PDF de comercios soportados (Coffee & Tea, 17); **falta contrastar contra /merchants en Telegram**
- [ ] 5. Mi equipo tiene un líder definido para recibir la API key por Telegram: capitán Fernando Vargas; **falta que confirme que ya la recibió**
- [x] 6. No es una reserva de viaje ni una categoría restringida (café y granos)
- [x] 7. No hago scraping del checkout ni le paso datos crudos de tarjeta a un LLM (el agente no ve datos de tarjeta; el LLM solo estructura señales)
- [x] 8. No es un chatbot genérico de buscar, mostrar y comprar (predicción de stock + compra en grupo)
- [x] 9. Sé a qué track aplico: **Track 1, Reap Most Worthwhile Problem** (confirmado por el equipo)

Envío:
- [x] Repo público enlazado (verificado: `gh repo view` → PUBLIC)
- [x] Video de demo de 1-2 min enlazado (1:45, carpeta de Drive; falta confirmar que el enlace abre sin iniciar sesión)
- [x] Descripción ≤ 5000 caracteres (2713)
- [x] Track elegido: solo Track 1
- [ ] Enviado por Fernando Vargas antes de las 23:39
