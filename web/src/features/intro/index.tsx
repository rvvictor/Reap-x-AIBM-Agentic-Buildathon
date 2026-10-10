export const order = 0;

const steps = [
  { n: 1, t: "El negocio ve su stock", d: "Cada cafetería ve cuánto tiene de cada producto frente a su stock base.", tag: "Simulado" },
  { n: 2, t: "El agente predice cuánto necesita", d: "Calcula un objetivo por producto según ventas, temporada y eventos, con motivos y confianza. El cálculo es código, no el LLM.", tag: "Simulado" },
  { n: 3, t: "Se juntan las faltas de los 4 negocios", d: "Las faltas se publican al agente global por MCP.", tag: "Simulado" },
  { n: 4, t: "El agente global compra en grupo", d: "Compara proveedores por costo entregado y reparte el ahorro: cada negocio paga menos que solo.", tag: "Simulado" },
  { n: 5, t: "Cada dueño autoriza su parte y se paga", d: "Cada negocio autoriza dentro de su tope. La tarjeta se registra en la página de Reap; la app nunca ve datos de tarjeta.", tag: "Reap sandbox (real)" },
  { n: 6, t: "Si algo cambia, el agente se detiene", d: "Si la cotización vence o el monto no coincide con lo autorizado, no cobra y pide aprobación.", tag: "Implementado" },
];

const css = `
.in{--ink:#2B1D14;--muted:#6B5A4D;--accent:#8A4B1F;--bg:#FAF6F0;--surface:#fff;--demo:#7A5AF8;--up:#1F7A4D;
 background:var(--bg);color:var(--ink);border-radius:12px;padding:20px;margin-bottom:16px}
@media (prefers-color-scheme:dark){.in{--ink:#F5ECE3;--muted:#BBA999;--bg:#17110D;--surface:#231A14}}
.in h1{font-size:1.5rem;font-weight:700;margin:0 0 6px}.in p{margin:0 0 12px;color:var(--muted);font-size:.9rem;line-height:1.45}
.in ol{list-style:none;margin:0;padding:0;display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.in li{background:var(--surface);border-radius:12px;padding:12px 14px;box-shadow:0 1px 2px rgb(0 0 0/.08);font-size:.8125rem}
.in b{display:block;font-size:.9rem;margin-bottom:2px}.in .n{color:var(--accent);font-weight:700;margin-right:6px}
.in .tag{display:inline-block;margin-top:6px;font-size:.625rem;padding:2px 7px;border-radius:999px;border:1px solid var(--demo);color:var(--demo)}
.in .real{border-color:var(--up);color:var(--up)}
.in .proof{margin-top:12px;background:var(--surface);border-left:4px solid var(--up);border-radius:8px;padding:10px 14px;font-size:.8125rem}
`;

export default function Intro() {
  return (
    <section className="in" aria-labelledby="intro-title">
      <style>{css}</style>
      <h1 id="intro-title">Bodega: compra en grupo para negocios pequeños</h1>
      <p>
        Los negocios pequeños fijan un stock y pierden ventas o dinero parado. Bodega le da a cada uno un
        <strong> objetivo de stock dinámico por producto</strong> y un <strong>agente global</strong> que junta las faltas de
        varios negocios, compara proveedores y consigue que <strong>paguen menos juntos que solos</strong>, con
        autorización de cada dueño. Abajo puedes recorrer la demo; los datos de negocios y ahorros son simulados
        (<code>demo_data</code>), el pago usa el sandbox de Reap.
      </p>
      <ol>
        {steps.map((s) => (
          <li key={s.n}>
            <b><span className="n">{s.n}</span>{s.t}</b>
            {s.d}
            <br />
            <span className={s.tag.startsWith("Reap") ? "tag real" : "tag"}>{s.tag}</span>
          </li>
        ))}
      </ol>
      <div className="proof">
        <strong>Prueba real en el sandbox de Reap:</strong> búsqueda de productos, cotización (31.11 USD con envío),
        inscripción de tarjeta con aprobación humana y checkout <strong>COMPLETED</strong>, pedido
        <code> ord_01M4J54ATSCJHV45X3MRDWS18F</code>. Esta página corre en modo demo con respuestas grabadas, sin claves en el servidor.
      </div>
    </section>
  );
}
