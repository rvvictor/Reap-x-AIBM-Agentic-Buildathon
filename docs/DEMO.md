# Demo · Bodega

Guion del video de 1-2 min (plan B si falla la red) y del pitch en vivo. Todo corre con `DEMO_MODE=true`.
Todas las cifras de la demo son **simuladas** (`demo_data: true`); no hay fuente real para ellas.

## Antes de grabar

- [ ] `cp .env.example .env` (sin claves) y `DEMO_MODE=true`.
- [ ] `npm --prefix web run build && uv run uvicorn app.main:app --port 8000`.
- [ ] Navegador a 1280×720, animaciones reducidas. Abrir <http://localhost:8000>.
- [ ] Verificar que los pasos 1-5 funcionan sin red (apaga el wifi una vez para confirmarlo).
- [ ] Capturas reales de los pasos 2, 4 y 5 en `docs/img/` (pendiente: dependen de HACK-006/008/010).

## Guion (≈ 90 s)

| t | Pantalla | Qué se dice |
|---|---|---|
| 0:00-0:12 | Tabla de inventario de una cafetería | "Una cafetería pequeña fija su stock a ojo. Con el frío se queda sin café; en verano le sobra. Y pide sola, así que paga precio de lista." |
| 0:12-0:40 | Botón **Predecir stock** → objetivos con motivos y confianza | **Wow 1.** "El agente local calcula el objetivo de cada producto: historial, temporada y un evento cercano. El LLM solo convierte el evento en una señal validada; el número lo calcula código determinista." Mostrar un producto: base → nuevo y sus motivos. |
| 0:40-0:55 | **Detectar faltas** en los 4 negocios | "Las faltas de cuatro cafeterías se publican al agente global y se agrupan por producto." |
| 0:55-1:15 | Vista del agente global | **Wow 2.** "Compara proveedores por costo total entregado y reparte el ahorro. Si algún negocio saldría peor, se excluye." Señalar el ahorro por negocio (simulado). |
| 1:15-1:30 | Aprobación por negocio y orden | "Cada dueño autoriza su parte dentro de su tope de presupuesto, en el checkout sandbox de Reap. El agente nunca ve datos de tarjeta, y si la cotización vence se detiene y pide aprobación." |

Cierre (una frase): "Bodega sabe cuánto stock necesita cada producto y consigue que cuatro negocios paguen menos juntos que solos."

Ejemplo de generalización (solo para el pitch, no está en la demo): farmacia, paracetamol 10→20, antigripal 10→15, dolor de estómago 10→5.

## Plan B

- Si falla la red o el sandbox: `DEMO_MODE=true` ya usa las respuestas grabadas de `app/fixtures/reap/`. Esas respuestas son errores `401 INVALID_AUTH_HEADER` grabados (no hay clave); no presentarlas como un catálogo real.
- Si falla la app: usar el video grabado con estas mismas pantallas.
- Decir siempre que los datos son simulados y que no se observó un checkout `COMPLETED` en el sandbox, a menos que ya se haya verificado.

## Lo que NO afirmar

- Que el ahorro es medido: es simulado.
- Que los precios por volumen existen en Reap: no está verificado.
- Que el pago real funciona: solo sandbox, y HACK-008 aún no está integrada.
- Resultados de backtest: no hay todavía; si se muestran, rotularlos "simulado".

## Checklist de entrega

El envío en Gavel (descripción, enlaces) es HACK-012.
