import { useEffect, useState } from "react";

export const order = 10;

// Mirrors Product + Forecast from app/schemas/models.py (HACK-002 / HACK-004 contract).
type Row = {
  sku_id: string;
  name: string;
  unit: string;
  base: number;
  current: number;
  target: number;
  reasons: string[];
  confidence: number;
  demo_data: boolean;
};

const MOCK: Row[] = [
  { sku_id: "cafe-aurora:grano", name: "Cafe en grano 250 g", unit: "bolsa", base: 12, current: 7, target: 16, reasons: ["Temporada fria +20%", "Evento local fin de semana"], confidence: 0.82, demo_data: true },
  { sku_id: "cafe-aurora:filtros", name: "Filtros de papel V60", unit: "caja", base: 6, current: 4, target: 6, reasons: ["Sin senales relevantes"], confidence: 0.74, demo_data: true },
  { sku_id: "cafe-aurora:vasos", name: "Vasos 12 oz", unit: "paquete", base: 20, current: 9, target: 24, reasons: ["Evento local fin de semana"], confidence: 0.69, demo_data: true },
  { sku_id: "cafe-aurora:leche", name: "Leche de avena 1 L", unit: "caja", base: 10, current: 12, target: 8, reasons: ["Lluvia reduce trafico -15%"], confidence: 0.61, demo_data: true },
  { sku_id: "cafe-aurora:jarabe", name: "Jarabe de vainilla", unit: "botella", base: 5, current: 3, target: 6, reasons: ["Temporada fria +20%"], confidence: 0.77, demo_data: true },
];

type State = "loading" | "error" | "ready";

const css = `
.bz{--bg:#FAF6F0;--surface:#fff;--ink:#2B1D14;--muted:#6B5A4D;--accent:#8A4B1F;--up:#1F7A4D;--down:#B3472A;--demo:#7A5AF8;
 background:var(--bg);color:var(--ink);border-radius:12px;padding:20px;font-variant-numeric:tabular-nums}
@media (prefers-color-scheme:dark){.bz{--bg:#17110D;--surface:#231A14;--ink:#F5ECE3;--muted:#BBA999}}
.bz h1{font-size:1.25rem;font-weight:650;margin:0}
.bz .sub{color:var(--muted);font-size:.8125rem;margin:2px 0 12px}
.bz .badge{display:inline-block;font-size:.625rem;line-height:1;padding:3px 6px;border-radius:999px;border:1px solid var(--demo);color:var(--demo);vertical-align:middle;margin-left:6px}
.bz .list{display:grid;gap:8px}
.bz .row{background:var(--surface);border-radius:12px;padding:10px 14px;box-shadow:0 1px 2px rgb(0 0 0/.08);display:grid;gap:6px 16px;
 grid-template-columns:minmax(0,2fr) repeat(3,minmax(0,.7fr)) minmax(0,2fr) minmax(0,.8fr);align-items:center;font-size:.8125rem}
.bz .head{background:none;box-shadow:none;color:var(--muted);font-size:.6875rem;text-transform:uppercase;letter-spacing:.04em;padding-top:0;padding-bottom:0}
.bz .lbl{display:none}
.bz .name{font-weight:600}
.bz .up{color:var(--up);font-weight:650}.bz .down{color:var(--down);font-weight:650}
.bz .reasons{color:var(--muted);font-size:.75rem;margin:0;padding:0;list-style:none}
.bz .bar{height:6px;border-radius:3px;background:color-mix(in srgb,var(--muted) 25%,transparent);overflow:hidden}
.bz .bar>i{display:block;height:100%;background:var(--accent)}
.bz .state{background:var(--surface);border-radius:12px;padding:28px;text-align:center;color:var(--muted)}
.bz button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:8px 14px;font:inherit;cursor:pointer;margin-top:10px}
.bz button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.bz .sk{height:44px;border-radius:12px;background:color-mix(in srgb,var(--muted) 18%,transparent);animation:bzp 1.2s ease-in-out infinite}
@keyframes bzp{50%{opacity:.5}}
@media (prefers-reduced-motion:reduce){.bz .sk{animation:none}}
@media (max-width:720px){
 .bz{padding:14px}.bz .head{display:none}
 .bz .row{grid-template-columns:1fr 1fr 1fr}.bz .name,.bz .reasons,.bz .conf{grid-column:1/-1}
 .bz .lbl{display:block;color:var(--muted);font-size:.625rem;text-transform:uppercase}
}`;

function initialState(): State {
  const q = new URLSearchParams(window.location.search).get("state");
  return q === "error" || q === "loading" ? q : "ready";
}

export default function Business() {
  const [state, setState] = useState<State>("loading");
  const [rows, setRows] = useState<Row[]>([]);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const forced = initialState();
    setState("loading");
    if (forced === "loading") return;
    const t = setTimeout(() => {
      if (forced === "error") return setState("error");
      setRows(new URLSearchParams(window.location.search).get("state") === "empty" ? [] : MOCK);
      setState("ready");
    }, 400);
    return () => clearTimeout(t);
  }, [tick]);

  return (
    <section className="bz" aria-labelledby="bz-title">
      <style>{css}</style>
      <h1 id="bz-title">
        Cafe Aurora · inventario y prediccion
        <span className="badge">demo_data</span>
      </h1>
      <p className="sub">Objetivo dinamico por producto segun senales de temporada, eventos y clima.</p>

      {state === "loading" && (
        <div className="list" role="status" aria-label="Cargando">
          {[0, 1, 2, 3, 4].map((i) => <div className="sk" key={i} />)}
        </div>
      )}

      {state === "error" && (
        <div className="state" role="alert">
          No pudimos cargar el inventario.
          <div><button onClick={() => setTick((n) => n + 1)}>Reintentar</button></div>
        </div>
      )}

      {state === "ready" && rows.length === 0 && (
        <div className="state">Aun no hay productos. Carga el inventario para ver la prediccion.</div>
      )}

      {state === "ready" && rows.length > 0 && (
        <div className="list">
          <div className="row head" aria-hidden="true">
            <span>Producto</span><span>Base</span><span>Actual</span><span>Objetivo</span><span>Motivos</span><span>Confianza</span>
          </div>
          {rows.map((r) => {
            const delta = r.target - r.base;
            return (
              <article className="row" key={r.sku_id}>
                <div className="name">{r.name}<span className="badge">demo_data</span></div>
                <div><span className="lbl">Base</span>{r.base} {r.unit}</div>
                <div><span className="lbl">Actual</span>{r.current}</div>
                <div className={delta >= 0 ? "up" : "down"}>
                  <span className="lbl">Objetivo</span>{r.target} ({delta >= 0 ? "+" : ""}{delta})
                </div>
                <ul className="reasons">{r.reasons.map((x) => <li key={x}>{x}</li>)}</ul>
                <div className="conf">
                  <span className="lbl">Confianza</span>{Math.round(r.confidence * 100)}%
                  <div className="bar" role="presentation"><i style={{ width: `${r.confidence * 100}%` }} /></div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
