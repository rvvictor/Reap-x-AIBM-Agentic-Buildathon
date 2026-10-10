import { useEffect, useId, useMemo, useState } from "react";

export const order = 12;

// Product + Business from app/schemas and app/fixtures/businesses (HACK-002).
// Per-SKU budget is a demo split of Business.budget_cap so the owner can edit it.
type Draft = {
  id: string;
  name: string;
  unit: string;
  base: string;
  min: string;
  max: string;
  budget: string;
};

const BUSINESS = {
  id: "cafe-aurora",
  name: "Cafe Aurora",
  budgetCap: 6000,
  source: "Business.budget_cap · app/fixtures/businesses/businesses.json",
};

const MOCK: Draft[] = [
  { id: "cafe-aurora:grano", name: "Cafe en grano 250 g", unit: "bolsa", base: "12", min: "5", max: "36", budget: "1927" },
  { id: "cafe-aurora:filtros", name: "Filtros de papel V60", unit: "caja", base: "6", min: "2", max: "18", budget: "282" },
  { id: "cafe-aurora:vasos", name: "Vasos 12 oz con tapa", unit: "paquete", base: "10", min: "4", max: "30", budget: "659" },
  { id: "cafe-aurora:leche", name: "Leche entera 1 L", unit: "litro", base: "30", min: "12", max: "90", budget: "452" },
  { id: "cafe-aurora:chai", name: "Te chai en polvo 1 kg", unit: "bolsa", base: "8", min: "3", max: "24", budget: "1196" },
  { id: "cafe-aurora:chocolate", name: "Chocolate en polvo 1 kg", unit: "bolsa", base: "8", min: "3", max: "24", budget: "831" },
  { id: "cafe-aurora:azucar", name: "Azucar estandar 1 kg", unit: "kg", base: "15", min: "6", max: "45", budget: "238" },
  { id: "cafe-aurora:jarabe", name: "Jarabe de vainilla 750 ml", unit: "botella", base: "5", min: "2", max: "15", budget: "415" },
];

type View = "loading" | "error" | "ready";

const css = `
.st{--bg:#FAF6F0;--surface:#fff;--ink:#2B1D14;--muted:#6B5A4D;--accent:#8A4B1F;--up:#1F7A4D;--down:#B3472A;--demo:#7A5AF8;
 background:var(--bg);color:var(--ink);border-radius:12px;padding:16px;margin-top:16px;font-variant-numeric:tabular-nums}
@media (prefers-color-scheme:dark){.st{--bg:#17110D;--surface:#231A14;--ink:#F5ECE3;--muted:#BBA999}}
.st h2{font-size:1.25rem;font-weight:650;margin:0}
.st .sub{color:var(--muted);font-size:.8125rem;margin:2px 0 10px}
.st .badge{display:inline-block;font-size:.625rem;line-height:1;padding:3px 6px;border-radius:999px;border:1px solid var(--demo);color:var(--demo);vertical-align:middle;margin-left:6px}
.st .cap{display:flex;justify-content:space-between;gap:12px;align-items:baseline;background:var(--surface);border-radius:12px;padding:10px 14px;box-shadow:0 1px 2px rgb(0 0 0/.08);margin-bottom:8px}
.st .cap strong{font-size:1.05rem}
.st .over{color:var(--down)}
.st .ok{color:var(--up)}
.st .list{display:grid;gap:8px}
.st .row{background:var(--surface);border-radius:12px;padding:10px 12px;box-shadow:0 1px 2px rgb(0 0 0/.08);display:grid;gap:8px 10px;grid-template-columns:minmax(9rem,1.4fr) repeat(4,minmax(0,1fr));align-items:end}
.st .hint{grid-column:1/-1}
.st .name{font-weight:600;font-size:.875rem;margin:0}
.st .unit{display:block;color:var(--muted);font-weight:450;font-size:.75rem}
.st label{display:grid;gap:2px;font-size:.6875rem;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
.st input{width:100%;box-sizing:border-box;background:var(--bg);color:var(--ink);border:1px solid color-mix(in srgb,var(--muted) 35%,transparent);border-radius:8px;padding:6px 8px;font:inherit;font-size:.875rem}
.st input:focus-visible,.st button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.st input[aria-invalid="true"]{border-color:var(--down)}
.st p.hint{color:var(--down);font-size:.75rem;text-transform:none;letter-spacing:0;margin:0}
.st .state{background:var(--surface);border-radius:12px;padding:28px;text-align:center;color:var(--muted)}
.st .actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px}
.st button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:8px 14px;font:inherit;cursor:pointer}
.st button[disabled]{opacity:.45;cursor:not-allowed}
.st button.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.st .saved{color:var(--up);font-size:.8125rem;margin:0}
.st .sk{height:52px;border-radius:12px;background:color-mix(in srgb,var(--muted) 18%,transparent);animation:stp 1.2s ease-in-out infinite}
@keyframes stp{50%{opacity:.5}}
@media (prefers-reduced-motion:reduce){.st .sk{animation:none}}
@media (max-width:720px){
 .st{padding:12px}
 .st .row{grid-template-columns:1fr 1fr}
 .st .name{grid-column:1/-1}
}`;

function queryMode(): View | "empty" {
  const value = new URLSearchParams(window.location.search).get("settings");
  if (value === "error" || value === "loading" || value === "empty") return value;
  return "ready";
}

function whole(value: string): number | null {
  if (!/^\d+$/.test(value)) return null;
  return Number(value);
}

function rowIssues(row: Draft): string | null {
  const base = whole(row.base);
  const min = whole(row.min);
  const max = whole(row.max);
  const budget = whole(row.budget);
  if (base === null || min === null || max === null || budget === null) {
    return "Usa enteros de 0 en adelante.";
  }
  if (min > base || base > max || min > max) {
    return "El mínimo no puede pasar la base, ni la base el máximo.";
  }
  return null;
}

export default function Settings() {
  const titleId = useId();
  const [view, setView] = useState<View>("loading");
  const [rows, setRows] = useState<Draft[]>([]);
  const [tick, setTick] = useState(0);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const mode = queryMode();
    setSaved(false);
    setView("loading");
    if (mode === "loading") return;
    const timer = window.setTimeout(() => {
      if (mode === "error") {
        setView("error");
        return;
      }
      setRows(mode === "empty" ? [] : MOCK.map((row) => ({ ...row })));
      setView("ready");
    }, 400);
    return () => window.clearTimeout(timer);
  }, [tick]);

  const issues = useMemo(() => rows.map(rowIssues), [rows]);
  const spent = rows.reduce((sum, row) => sum + (whole(row.budget) ?? 0), 0);
  const overCap = spent > BUSINESS.budgetCap;
  const invalid = issues.some(Boolean) || overCap || rows.length === 0;

  function update(id: string, key: "base" | "min" | "max" | "budget", value: string) {
    setSaved(false);
    setRows((current) => current.map((row) => (row.id === id ? { ...row, [key]: value } : row)));
  }

  return (
    <section className="st" aria-labelledby={titleId}>
      <style>{css}</style>
      <h2 id={titleId}>
        {BUSINESS.name} · configuración
        <span className="badge">demo_data</span>
      </h2>
      <p className="sub">
        Stock base, mínimo, máximo y presupuesto por producto. Fuente: Product en app/fixtures/businesses/products.json.
      </p>

      {view === "loading" && (
        <div className="list" role="status" aria-label="Cargando configuración">
          {[0, 1, 2].map((item) => <div className="sk" key={item} />)}
        </div>
      )}

      {view === "error" && (
        <div className="state" role="alert">
          No pudimos cargar la configuración del negocio.
          <div><button type="button" onClick={() => setTick((n) => n + 1)}>Reintentar</button></div>
        </div>
      )}

      {view === "ready" && rows.length === 0 && (
        <div className="state">Este negocio aún no tiene productos. Agrega el catálogo para definir límites.</div>
      )}

      {view === "ready" && rows.length > 0 && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (!invalid) setSaved(true);
          }}
        >
          <div className="cap">
            <span title={BUSINESS.source}>
              Tope del ciclo
              <strong className={overCap ? "over" : "ok"}> {spent.toLocaleString("es-MX")} / {BUSINESS.budgetCap.toLocaleString("es-MX")} MXN</strong>
            </span>
            <span className="badge">demo_data</span>
          </div>
          {overCap && <p className="hint" role="alert">La suma por producto supera el tope de {BUSINESS.budgetCap.toLocaleString("es-MX")} MXN.</p>}
          <div className="list">
            {rows.map((row, index) => {
              const problem = issues[index];
              const described = problem ? `${row.id}-err` : undefined;
              return (
                <article className="row" key={row.id}>
                  <h3 className="name">
                    {row.name}
                    <span className="unit">{row.unit} · {row.id}</span>
                  </h3>
                  <label>
                    Base
                    <input
                      inputMode="numeric"
                      aria-label={`Stock base de ${row.name}`}
                      title="Product.base_stock"
                      value={row.base}
                      aria-invalid={Boolean(problem)}
                      aria-describedby={described}
                      onChange={(event) => update(row.id, "base", event.target.value)}
                    />
                  </label>
                  <label>
                    Mínimo
                    <input
                      inputMode="numeric"
                      aria-label={`Stock mínimo de ${row.name}`}
                      title="Product.min_stock"
                      value={row.min}
                      aria-invalid={Boolean(problem)}
                      aria-describedby={described}
                      onChange={(event) => update(row.id, "min", event.target.value)}
                    />
                  </label>
                  <label>
                    Máximo
                    <input
                      inputMode="numeric"
                      aria-label={`Stock máximo de ${row.name}`}
                      title="Product.max_stock"
                      value={row.max}
                      aria-invalid={Boolean(problem)}
                      aria-describedby={described}
                      onChange={(event) => update(row.id, "max", event.target.value)}
                    />
                  </label>
                  <label>
                    Presupuesto
                    <input
                      inputMode="numeric"
                      aria-label={`Presupuesto de ${row.name}`}
                      title="Reparto de ejemplo de Business.budget_cap, MXN"
                      value={row.budget}
                      aria-invalid={Boolean(problem)}
                      aria-describedby={described}
                      onChange={(event) => update(row.id, "budget", event.target.value)}
                    />
                  </label>
                  {problem && <p className="hint" id={`${row.id}-err`}>{problem}</p>}
                </article>
              );
            })}
          </div>
          <div className="actions">
            <button type="submit" disabled={invalid}>Guardar configuración</button>
            <button
              type="button"
              className="ghost"
              onClick={() => {
                setRows(MOCK.map((row) => ({ ...row })));
                setSaved(false);
              }}
            >
              Restablecer ejemplo
            </button>
            {saved && (
              <p className="saved" role="status">
                Guardado en esta sesión. demo_data: true. No se envió a la API.
              </p>
            )}
          </div>
        </form>
      )}
    </section>
  );
}
