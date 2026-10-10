# Bodega · guion de video de 2 minutos

Duración objetivo **2:00**, incluidas apertura y cierre. Este archivo es un guion: **no acredita que exista un video grabado**. Grabar con la app local, mantener `demo_data · cifras simuladas` legible y esperar los estados finales antes de cortar. El pitch de 3 minutos está en [PITCH.md](PITCH.md).

## Preparación de la grabación

Desde el worktree asignado, con dependencias ya instaladas y sin claves:

```bash
set -a
source .uak-env
set +a
npm --prefix web run build && DEMO_MODE=true uv run uvicorn app.main:app --host 127.0.0.1 --port "$UAK_PORT"
```

Abrir `http://127.0.0.1:$UAK_PORT` en otra ventana. FastAPI sirve el build y la API; no hace falta iniciar Vite. Para detener este servidor al terminar: `bash .uak/bin/wt stop` desde este worktree. No copiar ni mostrar claves o archivos `.env`.

- Preparar dependencias con `uv sync` y `npm --prefix web ci` **antes** de desconectar la red.
- Grabar a 1280×720, con movimiento reducido. Revisar que texto, montos y etiquetas sean legibles; las capturas móviles opcionales son a 390×844.
- Reiniciar el servidor y abrir un contexto nuevo del navegador para repetir desde cero: hay estado en memoria y una marca de intento de checkout en `sessionStorage`.
- Usar solo la propuesta del bloque **Agente global** para el recorrido API; no mezclarla con el bloque independiente de pago compartido situado más abajo.
- Para el correo de demo usar `demo@example.com`, y para URL de regreso `https://example.com/return`: son valores sintéticos; no se visita un checkout externo en este recorrido demo.
- Antes de grabar, ensayar en **API con datos de ejemplo**: recalcular, preparar autorizaciones, autorizar a los negocios que realmente devuelve el servidor, inscribir, confirmar y enviar checkout. Comprobar **Pedido conciliado** y el importe del servidor. Después reiniciar para grabar.

## Tomas y voz en off

| Tiempo | Toma / acción real | Voz en off |
|---|---|---|
| 0:00–0:12 | Inventario de Café Aurora. Mantener el rótulo de datos demo visible. | «Un negocio pequeño decide cuánto reponer y compra solo. Bodega combina un objetivo de stock por producto con compras compartidas.» |
| 0:12–0:35 | Acercamiento a café: base 12, objetivo 16, motivos. La tabla ya aparece calculada; no hay botón “Predecir stock”. | «Este ejemplo muestra cómo cambia el objetivo según las señales. El backend hace el cálculo determinista con historial y límites; esta tabla usa ejemplos fijos. La confianza es heurística.» |
| 0:35–0:58 | Ir a `#global`, **Datos → Demo**. Mostrar total entregado y ahorro; bajar al reparto individual. | «Cuatro cafeterías agrupan veinte bolsas. En el fixture, el costo pasa de 5,892 a 4,524 pesos: 1,368 de ahorro simulado. Incluye envío e IVA y muestra el reparto por negocio.» |
| 0:58–1:10 | Seleccionar **API con datos de ejemplo** → **Recalcular propuesta**. Esperar a que termine “Comparando…”. | «Ahora el servidor calcula una propuesta con datos de ejemplo. Esta vista usa su propio precio de referencia; los montos pueden cambiar.» |
| 1:10–1:30 | **Preparar autorizaciones demo**, después **Autorizar API demo** para cada negocio visible. Mostrar topes y el estado **Todos autorizaron**. | «Cada negocio autoriza su parte dentro del tope. Estas autorizaciones se guardan en el servidor de demo; no son permisos de pago reales.» |
| 1:30–1:47 | Escribir correo y URL de regreso; **Inscribir demo** → **Confirmar ACTIVE demo** → **Enviar checkout demo**. Esperar **Pedido conciliado**, identificador e importe final. | «El checkout simulado concilia el pedido. Si cambia el monto o vence la orden, el servicio requiere nueva aprobación. No se mueve dinero real.» |
| 1:47–2:00 | Plano final del pedido; sobreimpreso: “Datos y checkout simulados · sandbox externo pendiente”. | «Bodega: objetivos por producto, ahorro compartido y control individual. La integración de Reap está desarrollada; su checkout completado en sandbox sigue pendiente de verificación.» |

Si los clics tardan más, usar cortes entre estados ya alcanzados; no acelerar el cambio de estado ni superponer un éxito inventado. No arrastrar a la vista API los montos de la vista Demo. Los botones de autorización de Demo solo afectan esa simulación local y no sustituyen las autorizaciones API.

## Plan B

1. **Sin red / sandbox indisponible:** mantener `DEMO_MODE=true` desde el inicio. El recorrido grabado usa API local y fixtures, no requiere Reap ni LLM externos. Comprobarlo antes apagando la red después del build; no afirmar que se probó sin conexión si no se hizo.
2. **Falla de la app:** reproducir una copia local del video grabado, por ejemplo `docs/demo-planb.mp4`, solo si previamente se comprobó que existe, se reproduce y contiene el estado final. Decir: «Mostramos una grabación de la demo con datos simulados». No publicar ni enviar el video automáticamente.
3. **Sin video disponible:** usar las capturas existentes en `e2e/screens/`, revisadas contra el build actual. Algunas capturas o el guion de `docs/DEMO.md` pueden preceder a HACK-010: no usarlas como prueba de los botones o estados API actuales. Si están desactualizadas, mostrar solo los componentes que realmente acrediten y explicar el resto verbalmente.
4. **Error en autorización o checkout:** mostrar el error o estado detenido. No llamar “pagado” a un pedido que no llegó a conciliado. Si el servidor devuelve un importe distinto, detener el recorrido y explicar la necesidad de nueva aprobación.

## Checklist de quien graba

- [ ] Cronometrar el pitch a 3:00 y la edición final a 1–2 minutos.
- [ ] Verificar la secuencia de botones con el build actual y esperar el estado final.
- [ ] Mantener etiquetas demo y fuentes; no mostrar datos privados.
- [ ] Distinguir tabla fija, cálculo API local y sandbox externo pendiente.
- [ ] Probar el recorrido sin red; guardar y reproducir la copia local de respaldo.
- [ ] Revisar audio, legibilidad y cortes; entregar el archivo al responsable humano del envío.

Fuentes del recorrido: [IDEA.md](../IDEA.md), [business/index.tsx](../web/src/features/business/index.tsx), [global/index.tsx](../web/src/features/global/index.tsx), [global/data.ts](../web/src/features/global/data.ts) y [global/payments.tsx](../web/src/features/global/payments.tsx). No se incluyen resultados de backtest ni descuentos reales de Reap.
