import { useEffect, useRef, useState } from 'react';
import { api } from '../../lib/api';
import { businesses, money, type Proposal } from './data';

type Share = { business_id: string; sku_id: string; amount: number; budget_cap: number; approved: boolean };
export type Ledger = { proposal_id: string; currency: string; shares: Share[]; authorized_total: number; status: 'awaiting_approval' | 'ready' | 'needs_approval' | 'reconciled'; reason: string | null; order_id: string | null; checkout_id: string | null; final_amount: number | null; demo_data: true };
type Enrollment = { id: string; status: string; demo_data: true };
const record = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value);
const amount = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value) && value >= 0 && Number.isSafeInteger(Math.round(value * 100));
const nullableString = (value: unknown) => value === null || typeof value === 'string';
const statuses = new Set(['awaiting_approval', 'ready', 'needs_approval', 'reconciled']);
export function parseLedger(value: unknown, proposal: Proposal): Ledger {
  if (!record(value) || value.proposal_id !== proposal.id || value.currency !== 'MXN' || proposal.currency !== 'MXN' || value.demo_data !== true || !amount(value.authorized_total) || Math.round(value.authorized_total * 100) !== Math.round(proposal.total * 100) || typeof value.status !== 'string' || !statuses.has(value.status) || !nullableString(value.reason) || !nullableString(value.order_id) || !nullableString(value.checkout_id) || !(value.final_amount === null || amount(value.final_amount)) || !Array.isArray(value.shares)) throw new Error('El reparto de pago no corresponde a esta propuesta de demo.');
  const expected = new Map(proposal.allocations.map(row => [`${row.business_id}/${row.sku_id}`, Math.round(row.cost * 100)]));
  const seen = new Set<string>();
  let sum = 0;
  for (const share of value.shares) {
    if (!record(share) || typeof share.business_id !== 'string' || typeof share.sku_id !== 'string' || !amount(share.amount) || !amount(share.budget_cap) || typeof share.approved !== 'boolean') throw new Error('La autorización contiene datos inválidos.');
    const key = `${share.business_id}/${share.sku_id}`;
    const cents = Math.round(share.amount * 100);
    if (seen.has(key) || expected.get(key) !== cents) throw new Error('El reparto cambió o tiene negocios duplicados.');
    seen.add(key); sum += cents;
  }
  if (seen.size !== expected.size || sum !== Math.round(proposal.total * 100)) throw new Error('El reparto no conserva el costo total.');
  return value as Ledger;
}
function parseEnrollment(value: unknown): Enrollment {
  if (!record(value) || typeof value.id !== 'string' || !value.id || !['REQUIRES_ACTION', 'ACTIVE'].includes(String(value.status)) || value.demo_data !== true) throw new Error('El enrollment no cumple el contrato de demo.');
  return value as Enrollment;
}
const statusNames: Record<Ledger['status'], string> = { awaiting_approval: 'Pendiente de autorización', ready: 'Todos autorizaron', needs_approval: 'Requiere nueva aprobación', reconciled: 'Pedido conciliado' };

export default function PaymentControls({ proposal }: { proposal: Proposal }) {
  const [ledger, setLedger] = useState<Ledger | null>(null);
  const [enrollment, setEnrollment] = useState<Enrollment | null>(null);
  const [email, setEmail] = useState('');
  const [returnUrl, setReturnUrl] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const storageKey = `bodega-checkout-attempt:${proposal.id}`;
  const [attempted, setAttempted] = useState(() => sessionStorage.getItem(storageKey) !== null);
  const active = useRef(true);
  const generation = useRef(0);
  const lock = useRef(false);
  useEffect(() => { active.current = true; return () => { active.current = false; generation.current += 1; }; }, []);
  function valid(token: number) { return active.current && generation.current === token; }
  async function request(path: string, token: number, body?: object, actor?: string): Promise<unknown> {
    if (body) {
      const config = await api<{ demo_mode: boolean }>('/config', { signal: AbortSignal.timeout(15000) });
      if (config.demo_mode !== true) throw new Error('Esta pantalla autoriza únicamente DEMO_MODE.');
    }
    if (!valid(token)) throw new Error('La propuesta cambió; acción cancelada.');
    return api<unknown>(`/payments${path}`, { method: body ? 'POST' : 'GET', headers: { 'Content-Type': 'application/json', ...(actor ? { 'X-Demo-Business': actor } : {}) }, ...(body ? { body: JSON.stringify(body) } : {}), signal: AbortSignal.timeout(15000) });
  }
  async function run(action: (token: number) => Promise<void>) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError('');
    const token = generation.current;
    try { await action(token); }
    catch (cause) { if (valid(token)) setError(cause instanceof Error ? cause.message : 'No se pudo actualizar el pedido.'); }
    finally { lock.current = false; if (valid(token)) setBusy(false); }
  }
  async function read(token: number) {
    const next = parseLedger(await request(`/ledgers/${encodeURIComponent(proposal.id)}`, token), proposal);
    if (valid(token)) setLedger(next);
    return next;
  }
  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => { if (!cancelled && sessionStorage.getItem(storageKey)) void run(async token => { await read(token); }); });
    return () => { cancelled = true; };
  }, []);
  async function approve(id: string) {
    await run(async token => {
      const next = parseLedger(await request(`/ledgers/${encodeURIComponent(proposal.id)}/authorizations`, token, { business_id: id }, id), proposal);
      if (valid(token)) setLedger(next);
    });
  }
  async function enroll() {
    await run(async token => {
      const url = new URL(returnUrl);
      if (url.protocol !== 'https:' || !email.includes('@')) throw new Error('Ingresa correo y URL de regreso HTTPS.');
      const next = parseEnrollment(await request('/enrollments', token, { owner_id: businesses[0].id, email, return_url: url.href }));
      if (valid(token)) setEnrollment(next);
    });
  }
  async function confirm() {
    if (!enrollment) return;
    await run(async token => {
      const next = parseEnrollment(await request(`/enrollments/${encodeURIComponent(enrollment.id)}/confirm`, token, { demo_return: true }));
      if (next.id !== enrollment.id || next.status !== 'ACTIVE') throw new Error('El enrollment aún no está ACTIVE.');
      if (valid(token)) setEnrollment(next);
    });
  }
  async function checkout() {
    if (!ledger || enrollment?.status !== 'ACTIVE' || attempted) return;
    await run(async token => {
      const fresh = await read(token);
      if (fresh.status !== 'ready' || fresh.order_id || (fresh.final_amount !== null && Math.round(fresh.final_amount * 100) !== Math.round(proposal.total * 100)) || !fresh.shares.every(row => row.approved && row.amount <= row.budget_cap)) throw new Error('El servidor cambió la autorización. Consulta y vuelve a aprobar.');
      if (!valid(token)) return;
      sessionStorage.setItem(storageKey, 'attempted'); setAttempted(true);
      // The HACK-008 fixture variant is used only behind the DEMO_MODE write guard.
      try {
        const next = parseLedger(await request('/checkouts', token, { proposal_id: proposal.id, enrollment_id: enrollment.id, variant_id: '3c90c3cc-0d44-4b50-8888-8dd25736052a', email, return_url: returnUrl } ), proposal);
        if (valid(token)) setLedger(next);
      } finally { if (valid(token)) await read(token); }
    });
  }
  const ids = [...new Set(ledger?.shares.map(row => row.business_id) ?? [])];
  const approvedCount = ids.filter(id => ledger?.shares.filter(row => row.business_id === id).every(row => row.approved)).length;
  const mismatched = ledger?.final_amount !== null && ledger?.final_amount !== undefined && Math.round(ledger.final_amount * 100) !== Math.round(proposal.total * 100);
  const ready = ledger?.status === 'ready' && !ledger.order_id && !mismatched && ledger.shares.every(row => row.approved && row.amount <= row.budget_cap);
  return <>
    <div className="panel-title"><h2>Cada dueño tiene la última palabra</h2><span className="muted">{approvedCount}/{ids.length || proposal.allocations.length} · estado de API</span></div>
    {error && <div role="alert" className="global-error">{error}</div>}
    {!ledger ? <button className="secondary-button" disabled={busy || attempted} onClick={() => void run(async token => { const next = parseLedger(await request('/ledgers', token, { proposal_id: proposal.id }), proposal); if (valid(token)) setLedger(next); })}>{busy ? 'Preparando…' : 'Preparar autorizaciones demo'}</button> : <>
      <div className="business-list">{ids.map(id => {
        const business = businesses.find(row => row.id === id);
        const rows = ledger.shares.filter(row => row.business_id === id);
        const cost = rows.reduce((sum, row) => sum + row.amount, 0);
        const savings = proposal.allocations.filter(row => row.business_id === id).reduce((sum, row) => sum + row.savings, 0);
        const approved = rows.every(row => row.approved);
        return <div className="business-row" key={id}><div className="business-name"><strong>{business?.name ?? id}{ledger.order_id && <small className="payment-order" title={ledger.order_id}> · {statusNames[ledger.status]}</small>}</strong><span>{money(cost)} <small className="savings-text">ahorra {money(savings)}</small></span></div><span className="budget-label" title="Business.budget_cap del servidor">Tope MXN<strong>{money(rows[0].budget_cap)}</strong></span><button className={`approve-button ${approved ? 'is-approved' : ''}`} disabled={busy || attempted || approved || cost > rows[0].budget_cap || ledger.status === 'reconciled'} onClick={() => void approve(id)}>{approved ? 'Autorizado API' : 'Autorizar API demo'}</button></div>;
      })}</div>
      {!attempted && enrollment?.status !== 'ACTIVE' && <div className="payment-setup"><label>Correo del titular<input type="email" value={email} disabled={busy || !!enrollment} onChange={event => setEmail(event.target.value)} /></label><label>URL de regreso HTTPS<input type="url" value={returnUrl} disabled={busy || !!enrollment} onChange={event => setReturnUrl(event.target.value)} placeholder="https://…" /></label><button className="secondary-button" disabled={busy || !!enrollment || !email || !returnUrl} onClick={() => void enroll()}>Inscribir demo</button><button className="secondary-button" disabled={busy || !enrollment || enrollment.status === 'ACTIVE'} onClick={() => void confirm()}>Confirmar ACTIVE demo</button></div>}
      <div className="payment-checkout"><span className="muted">{statusNames[ledger.status]}{enrollment ? ` · ${enrollment.status}` : ''}</span><button className="primary-button" hidden={attempted} disabled={busy || !ready || enrollment?.status !== 'ACTIVE' || attempted} onClick={() => void checkout()}>Enviar checkout demo</button>{attempted && <button className="secondary-button" disabled={busy} onClick={() => void run(async token => { await read(token); })}>Consultar pedido</button>}</div>
      {ledger.reason && <p className="cap-error">API: {ledger.reason}</p>}
      {ledger.order_id && <p className="panel-footnote" title={ledger.order_id}>Pedido API: {ledger.order_id}</p>}
      {ledger.final_amount !== null && <p className="panel-footnote">finalAmount del servidor: {money(ledger.final_amount)} {mismatched ? '· Importe distinto: nuevos checkouts bloqueados.' : ''}</p>}
    </>}
    <p className="panel-footnote">demo_data · titular: Café Aurora. Topes del catálogo; autorización y pedido simulados, sin dinero real.</p>
  </>;
}
