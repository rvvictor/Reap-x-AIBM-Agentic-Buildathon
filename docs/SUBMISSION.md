# Entrega en Gavel · Bodega

Envío: https://gavel-65labs.vercel.app/submit/74oz5tv1cfzllzh392gy1rqzvx4m1vop
**Quién envía: Fernando Vargas (capitán).** Plazo oficial: 2026-10-09 21:00 CDMX · envío interno: 20:40.

## Campos del formulario (copiar y pegar)
| Campo | Valor |
|---|---|
| Team name | Axolutions |
| Team captain | Fernando Vargas |
| Contact email | vargas.fer2442@gmail.com |
| Project link | https://github.com/rvvictor/Reap-x-AIBM-Agentic-Buildathon |
| Demo video link | **PENDIENTE**: pegar el enlace de YouTube/Drive cuando exista (video de 1-2 min; plan B en `docs/demo-planb.mp4`) |
| Team members | Fernando Vargas, Victor Ruiz, Sebastian Jara, Javier Reyna, Dylan Martinez |
| Sponsor prize tracks (máx. 2) | Reap Most Worthwhile Problem |

El track "Reap Best Bridge Onchain-Real World" **no** se elige: el proyecto no usa onchain (decisión del equipo pendiente de confirmar por Fernando).

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
> Los 9 puntos oficiales están en la página del evento (https://aibuilders.mx/reap) y **no están copiados en el repo**. Pega aquí el texto oficial y marca cada uno. Abajo, los requisitos que sí constan en `.uak/PROJECT.md`; marcar solo con evidencia.

- [ ] Usa el Agentic module de Reap (búsqueda → cotización → checkout en sandbox) y es central al producto
- [ ] Solo sandbox, sin dinero real, solo comercios soportados
- [ ] No hay viajes, categorías restringidas ni scraping del checkout; ningún dato de tarjeta llega a un LLM
- [ ] No es un chatbot genérico de buscar-mostrar-comprar
- [ ] Repo público/accesible enlazado
- [ ] Video de demo de 1-2 min enlazado (con plan B `docs/demo-planb.mp4`)
- [ ] Descripción ≤ 5000 caracteres pegada
- [ ] Tracks elegidos (máx. 2)
- [ ] Enviado por Fernando Vargas antes de las 20:40
