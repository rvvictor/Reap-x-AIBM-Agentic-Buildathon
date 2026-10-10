# Idea general · Red de agentes de abasto con predicción de stock

> Nombre del producto: **por definir**. Estado: idea definida por el equipo Axolutions durante el Reap x AIBM Agentic Buildathon (2026-10-09).
> Origen: conversación con Codex (`ideaprimaria`) + decisiones del equipo. Las cifras de ahorro son hipótesis hasta validarse (ver §9).

## 1. Resumen en una frase
Cada negocio tiene un **agente local** que predice cuánto stock de cada producto necesitará (por temporada, historial y eventos cercanos) y detecta lo que le va a faltar; un **agente global** agrupa esas faltas de muchos negocios, las compara entre proveedores por categoría y compra en volumen para que cada negocio pague menos que comprando por su cuenta, todo dentro de los límites que fija cada dueño.

## 2. El problema (cualquier negocio que compra para revender o consumir)
- Farmacias, cafeterías, restaurantes, tiendas, consultorios, talleres: todos reponen inventario con una regla fija ("siempre 10 unidades") o a ojo.
- Un stock fijo falla dos veces: **se acaba lo que sube de demanda** (venta perdida) y **sobra lo que baja** (capital inmovilizado, merma, caducidad).
- Un negocio pequeño compra en cantidades chicas: paga precio alto de mayoreo, envío por pedido e impuestos sin escala.
- Fuera de alcance por ahora: negocios que ya tienen contrato recurrente con distribuidores. No se consideran en esta versión.

## 3. Núcleo del producto: predicción de stock por producto
El dueño define un **stock base** por producto (ej. 10 unidades). El agente local lo convierte en un **stock objetivo dinámico por producto**, no por categoría:

| Ejemplo (farmacia, solo ilustrativo) | Base | Objetivo dinámico (temporada de frío) |
|---|---:|---:|
| Paracetamol | 10 | 20 |
| Antigripal | 10 | 15 |
| Claritromicina | 10 | 17 |
| Medicamento para dolor de estómago | 10 | 5 |

El mismo mecanismo aplica a cualquier giro (café en temporada de frío, helado en calor, útiles en regreso a clases, flores en febrero y mayo).

### Señales que alimentan la predicción
1. **Historial de ventas/consumo** del propio negocio (velocidad de venta por producto, tendencia).
2. **Temporada y estación** (calendario, clima de la zona).
3. **Eventos cercanos** (concentración en el palacio municipal, partido, feria, lluvia) que cambian la demanda de categorías concretas.
4. **Reglas del dueño**: stock mínimo y máximo, presupuesto, capacidad de almacenamiento, caducidad.
5. **Pedidos pendientes** y tiempo de entrega de cada proveedor.

### Cómo se calcula (principio de diseño)
- **El número lo calcula código determinista y verificable**, no el LLM: demanda esperada = velocidad de venta × factor de temporada × factor de evento, más colchón de seguridad por tiempo de entrega, acotado por mínimo/máximo del dueño y capacidad.
- **El LLM interpreta señales y explica**: convierte un evento o noticia en una señal estructurada (categorías afectadas, dirección, magnitud acotada, fuente citada) validada contra un esquema antes de usarse; y redacta la explicación "por qué subió el objetivo".
- Cada recomendación muestra: stock actual, objetivo base, objetivo dinámico, **motivos** y nivel de confianza. Si el dato es dudoso, pide confirmación antes de comprar.

## 4. Agente global: compra agrupada y comparación de proveedores
Recibe de los agentes locales solo lo necesario (producto, cantidad, fecha, sustitutos aceptables). Las ventas, márgenes y recetas de cada negocio permanecen privadas.

1. **Agrupa** faltas de varios negocios por categoría y producto equivalente.
2. **Compara** proveedores por categoría: precio unitario, envío, impuestos, disponibilidad y fecha de entrega (costo total entregado).
3. **Propone** una compra conjunta con el ahorro por negocio frente a su "precio a vencer" (lo que pagaría solo).
4. **Pide autorización** a cada negocio dentro de su presupuesto y sustituciones permitidas.
5. **Ejecuta** la compra mediante el Agentic module de Reap (sandbox) y reparte costo y entrega por negocio.

Promesa comercial: "tu producto, al menos $1 más barato que tu mejor precio de mayoreo", porque el agente global compra "mayoreo del mayoreo": menos costo de envío por unidad, mejor precio por volumen e impuestos y cargos amortizados.

### Reglas de seguridad y confianza
- Nunca comprar más de lo útil solo para alcanzar un descuento: el ahorro descuenta almacenamiento, merma y entrega.
- Cada negocio debe ganar individualmente; el reparto es visible y aceptado antes de pagar.
- Antes de pagar se vuelve a validar disponibilidad y precio; si algo cambia fuera de lo autorizado, **el agente se detiene y pide aprobación**.
- El pago pasa siempre por la página de aprobación de Reap; el agente nunca ve datos de tarjeta.

## 5. Flujo de punta a punta
Stock base del dueño → predicción de objetivo dinámico → faltas detectadas → agrupación en agente global → comparación de proveedores → propuesta con ahorro por negocio → autorización de cada dueño → cotización y checkout (Reap) → seguimiento de entrega → el agente aprende de lo vendido.

## 6. Generalización a cualquier negocio
Un negocio se describe con: catálogo (SKU, categoría, unidad), stock actual, stock base y límites, historial de ventas, ubicación (para clima/eventos), presupuesto y permisos. Nada del algoritmo depende del giro; cambian solo las señales relevantes (la gripa afecta a una farmacia, no a una ferretería). Farmacia, cafetería, restaurante, papelería, tienda de abarrotes y consultorio entran con el mismo agente local.

## 7. Cliente y valor
- **Cliente:** dueños de negocios pequeños y medianos sin contrato recurrente con distribuidores.
- **Valor:** menos ventas perdidas, menos capital inmovilizado, y menor costo de compra por poder colectivo, sin cambiar de proveedor a la fuerza.
- **Modelo de ingreso (hipótesis):** porcentaje del ahorro generado o suscripción por negocio. Por validar.

## 8. Alcance para el hackathon (3 horas, sandbox)
**Dentro:** agente local con predicción por producto y explicación; agente global con agrupación y comparación por categoría; propuesta con ahorro por negocio; autorización y compra por Reap en sandbox; datos de negocios simulados y etiquetados `demo_data: true`.
**Fuera:** contratos con distribuidores, logística propia, perecederos complejos, cobros recurrentes (los mandates de Reap no están disponibles), compras reales.
**Giro de la demo:** cafeterías (la categoría Coffee & Tea es la más cubierta por los comercios soportados), presentando la farmacia como ejemplo de generalización.

## 9. Riesgos y supuestos por validar
- Los comercios soportados por Reap son tiendas de consumo; **no está verificado** que ofrezcan precio por volumen. Si no, el ahorro de la demo se basa en comparar proveedores y consolidar envío, y cualquier escala de precios se etiqueta como simulada.
- Reap guarda una tarjeta por inscripción; el reparto de pago por negocio se resuelve en nuestra capa (libro interno) y habrá que comprobar qué demuestra mejor en sandbox.
- Las farmacias no aparecen entre los comercios soportados; usar la categoría correcta en la demo.
- Los datos históricos de la demo son sintéticos; la precisión de la predicción se reporta como backtest sobre datos simulados, no como resultado real.
- Competidores/antecedentes de compra colectiva: Foodbuy (GPO) y Choco (pedidos de restaurantes). Nuestra diferencia: predicción anticipada por producto + grupos dinámicos + permisos individuales.
