import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export const order = 30;

type Share = {
  business_id: string;
  sku_id: string;
  amount: number;
  budget_cap: number;
  approved: boolean;
};

type Ledger = {
  proposal_id: string;
  currency: string;
  shares: Share[];
  authorized_total: number;
  status: string;
  reason: string | null;
  order_id: string | null;
  final_amount: number | null;
  demo_data: boolean;
};

type Enrollment = { id: string; status: string };

type State = "loading" | "error" | "empty" | "ready";

const RETURN_URL = "https://bodega.demo/payments/return";
const VARIANT = "3c90c3cc-0d44-4b50-8888-8dd25736052a";

const css = `
.ck{--bg:#FAF6F0;--surface:#fff;--ink:#2B1D14;--muted:#6B5A4D;--accent:#8A4B1F;--up:#1F7A4D;--down:#B3472A;--demo:#7A5AF8;
 background:var(--bg);color:var(--ink);border-radius:12px;padding:20px;margin-top:24px;font-variant-numeric:tabular-nums}
@media (prefers-color-scheme:dark){.ck{--bg:#17110D;--surface:#231A14;--ink:#F5ECE3;--muted:#BBA999}}
.ck h1{font-size:1.25rem;font-weight:650;margin:0}
.ck .sub{color:var(--muted);font-size:.8125rem;margin:2px 0 12px}
.ck .badge{display:inline-block;font-size:.625rem;line-height:1;padding:3px 6px;border-radius:999px;border:1px solid var(--demo);color:var(--demo);vertical-align:middle;margin-left:6px}
.ck .row{background:var(--surface);border-radius:12px;padding:10px 14px;box-shadow:0 1px 2px rgb(0 0 0/.08);display:grid;grid-template-columns:1.4fr .8fr .8fr .8fr auto;gap:8px;align-items:center;font-size:.8125rem;margin-bottom:8px}
.ck .state{background:var(--surface);border-radius:12px;padding:28px;text-align:center;color:var(--muted)}
.ck button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:8px 14px;font:inherit;cursor:pointer}
.ck button:disabled{opacity:.45;cursor:not-allowed}
.ck button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.ck .ok{color:var(--up);font-weight:650}.ck .stop{color:var(--down);font-weight:650}
.ck .note{color:var(--muted);font-size:.75rem;margin:8px 0 0}
.ck .sk{height:44px;border-radius:12px;background:color-mix(in srgb,var(--muted) 18%,transparent);margin-bottom:8px}
@media (prefers-reduced-motion:reduce){.ck .sk{animation:none}}
@media (max-width:720px){.ck{padding:14px}.ck .row{grid-template-columns:1fr 1fr}}
`;

function forced(): State | null {
  const value = new URLSearchParams(window.location.search).get("pay");
  return value === "loading" || value === "error" || value === "empty" ? value : null;
}

export default function Checkout() {
  const [state, setState] = useState<State>("loading");
  const [ledger, setLedger] = useState<Ledger | null>(null);
  const [enrollment, setEnrollment] = useState<Enrollment | null>(null);
  const [message, setMessage] = useState("");
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const mode = forced();
    setState("loading");
    setMessage("");
    if (mode === "loading") return;
    if (mode === "error") return setState("error");
    if (mode === "empty") return setState("empty");
    let cancel = false;
    (async () => {
      try {
        const proposals = await api<Array<{ id: string }>>("/global/proposals");
        if (cancel) return;
        if (proposals.length === 0) return setState("empty");
        const book = await api<Ledger>("/payments/ledgers", {
          method: "POST",
          body: JSON.stringify({ proposal_id: proposals[0].id }),
        });
        if (!cancel) {
          setLedger(book);
          setState("ready");
        }
      } catch {
        if (!cancel) setState("error");
      }
    })();
    return () => {
      cancel = true;
    };
  }, [tick]);

  async function prepare() {
    setState("loading");
    try {
      const proposals = await api<Array<{ id: string }>>("/global/proposals", {
        method: "POST",
        body: JSON.stringify({
          needs: [
            { business_id: "cafe-aurora", sku_id: "cafe-aurora:grano", product_name: "Cafe en grano 250 g", category: "cafe-grano", qty: 2, needed_by: "2030-01-01", accepted_equivalents: ["cafe-brasa:grano"] },
            { business_id: "cafe-brasa", sku_id: "cafe-brasa:grano", product_name: "Cafe en grano 250 g", category: "cafe-grano", qty: 2, needed_by: "2030-01-01", accepted_equivalents: ["cafe-aurora:grano"] },
          ],
        }),
      });
      const book = await api<Ledger>("/payments/ledgers", {
        method: "POST",
        body: JSON.stringify({ proposal_id: proposals[0].id }),
      });
      setLedger(book);
      setState("ready");
    } catch {
      setState("error");
    }
  }

  async function approve(businessId: string) {
    if (!ledger) return;
    const book = await api<Ledger>(`/payments/ledgers/${ledger.proposal_id}/authorizations`, {
      method: "POST",
      body: JSON.stringify({ business_id: businessId }),
    });
    setLedger(book);
  }

  async function startEnrollment() {
    const created = await api<Enrollment>("/payments/enrollments", {
      method: "POST",
      body: JSON.stringify({ owner_id: "bodega", email: "ops@bodega.example", return_url: RETURN_URL }),
    });
    setEnrollment(created);
    setMessage("Tarjeta en inscripción EXTERNAL. Confirma ACTIVE antes de cobrar.");
  }

  async function confirmCard() {
    if (!enrollment) return;
    const confirmed = await api<Enrollment>(`/payments/enrollments/${enrollment.id}/confirm`, {
      method: "POST",
      body: JSON.stringify({ demo_return: true }),
    });
    setEnrollment(confirmed);
    setMessage("Inscripción ACTIVE. El cobro ya puede usar esta tarjeta.");
  }

  async function charge() {
    if (!ledger || !enrollment) return;
    try {
      const book = await api<Ledger>("/payments/checkouts", {
        method: "POST",
        body: JSON.stringify({
          proposal_id: ledger.proposal_id,
          enrollment_id: enrollment.id,
          variant_id: VARIANT,
          email: "ops@bodega.example",
          return_url: RETURN_URL,
        }),
      });
      setLedger(book);
      setMessage(book.reason ?? "Pedido conciliado contra finalAmount.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "El cobro se detuvo.");
    }
  }

  const businesses = [...new Set(ledger?.shares.map((row) => row.business_id) ?? [])];

  return (
    <section className="ck" aria-labelledby="ck-title">
      <style>{css}</style>
      <h1 id="ck-title">
        Pago compartido
        <span className="badge">demo_data</span>
      </h1>
      <p className="sub">Cada negocio autoriza su parte. Una tarjeta Reap cobra el total y el libro interno reparte.</p>

      {state === "loading" && <div className="sk" role="status" aria-label="Cargando" />}
      {state === "error" && (
        <div className="state" role="alert">
          No pudimos cargar el reparto.
          <div><button onClick={() => setTick((n) => n + 1)}>Reintentar</button></div>
        </div>
      )}
      {state === "empty" && (
        <div className="state">
          No hay una propuesta lista para cobrar.
          <div><button onClick={prepare}>Preparar propuesta demo</button></div>
        </div>
      )}
      {state === "ready" && ledger && (
        <div>
          {businesses.map((businessId) => {
            const rows = ledger.shares.filter((row) => row.business_id === businessId);
            const amount = rows.reduce((sum, row) => sum + row.amount, 0);
            return (
              <article className="row" key={businessId}>
                <strong>{businessId}</strong>
                <span title="Suma de Allocation.cost">{amount.toFixed(2)} {ledger.currency}</span>
                <span title="Business.budget_cap">tope {rows[0].budget_cap.toFixed(0)}</span>
                <span className={rows.every((row) => row.approved) ? "ok" : "stop"}>
                  {rows.every((row) => row.approved) ? "autorizado" : "pendiente"}
                </span>
                <button disabled={rows.every((row) => row.approved)} onClick={() => approve(businessId)}>Autorizar</button>
              </article>
            );
          })}
          <p className="note">Autorizado {ledger.authorized_total.toFixed(2)} {ledger.currency}. Fuente del reparto: Allocation.cost. Fuente del cobro: Reap checkout.finalAmount.</p>
          <div className="row">
            <button onClick={startEnrollment}>Inscribir tarjeta</button>
            <button disabled={!enrollment || enrollment.status === "ACTIVE"} onClick={confirmCard}>Confirmar ACTIVE</button>
            <button disabled={ledger.status !== "ready" || enrollment?.status !== "ACTIVE"} onClick={charge}>Cobrar</button>
            <span className={ledger.status === "reconciled" ? "ok" : ledger.status === "needs_approval" ? "stop" : ""}>{ledger.status}</span>
          </div>
          {ledger.order_id && <p className="note">Pedido {ledger.order_id}. finalAmount {ledger.final_amount} {ledger.currency}.</p>}
          {message && <p className="note" role="status">{message}</p>}
        </div>
      )}
    </section>
  );
}
