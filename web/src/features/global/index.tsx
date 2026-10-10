import { useEffect, useRef, useState } from 'react';
import { ArrowRight, CheckCircle, Coffee, ShieldCheck, UsersThree } from '@phosphor-icons/react';
import { api } from '../../lib/api';
import { businesses, delivered, money, offers, parseRequestedProposals, proposalRequest, sampleProposal, type Proposal } from './data';
import './global.css';
import PaymentControls from './payments';

export const order = 20;
const statusNames: Record<Proposal['status'], string> = { draft: 'Borrador', pending_approval: 'Pendiente de autorización', approved: 'Autorizada', paid: 'Pagada según API', stopped: 'Detenida', failed: 'Fallida' };

export default function GlobalAgent() {
  const [mode, setMode] = useState<'demo' | 'api'>('demo');
  const [proposal, setProposal] = useState<Proposal | null>(sampleProposal);
  const [approved, setApproved] = useState<string[]>([]);
  const [caps, setCaps] = useState<Record<string, string>>(Object.fromEntries(businesses.map(business => [business.id, String(business.budget)])));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const refreshVersion = useRef(0);
  useEffect(() => {
    const showGlobal = () => { if (window.location.hash === '#global') requestAnimationFrame(() => document.getElementById('global')?.scrollIntoView({ block: 'start', behavior: 'instant' })); };
    showGlobal(); window.addEventListener('hashchange', showGlobal);
    return () => window.removeEventListener('hashchange', showGlobal);
  }, []);

  function changeMode(next: 'demo' | 'api') {
    refreshVersion.current += 1;
    setMode(next); setLoading(false); setApproved([]); setError(''); setProposal(next === 'demo' ? sampleProposal() : null);
  }
  async function refresh() {
    const version = ++refreshVersion.current;
    setLoading(true); setError(''); setApproved([]);
    try {
      let next: Proposal | null;
      if (mode === 'api') {
        const results = parseRequestedProposals(await api<unknown>('/global/proposals', { method: 'POST', body: JSON.stringify(proposalRequest), signal: AbortSignal.timeout(15000) }));
        next = results[0] ?? null;
      } else {
        await new Promise(resolve => setTimeout(resolve, 150));
        next = sampleProposal();
      }
      if (version === refreshVersion.current) setProposal(next);
    } catch (cause) { if (version === refreshVersion.current) setError(cause instanceof Error ? cause.message : 'No se pudo recuperar la propuesta.'); }
    finally { if (version === refreshVersion.current) setLoading(false); }
  }
  const allocations = proposal?.allocations ?? [];
  const ids = [...new Set(allocations.map(allocation => allocation.business_id))];
  const groupQuantity = allocations.reduce((sum, allocation) => sum + allocation.qty, 0);
  const approvedCount = mode === 'demo' ? approved.length : ids.filter(id => allocations.filter(row => row.business_id === id).every(row => row.approved)).length;
  const allApproved = ids.length > 0 && ids.every(id => approved.includes(id));
  const demo = mode === 'demo';
  const provenance = demo ? 'demo_data · cifras simuladas' : 'demo_data · cálculo de API';

  return <section id="global" className="bodega-global" aria-labelledby="global-title">
    <header className="global-header">
      <div className="global-brand"><Coffee size={24} weight="duotone" /><strong>Bodega</strong><span>/ Agente global</span></div>
      <div className="global-controls"><span className="demo-label">{demo ? 'demo_data · simulación' : 'API · datos de ejemplo'}</span><label className="mode-label">Datos<select value={mode} onChange={event => changeMode(event.target.value as 'demo' | 'api')}><option value="demo">Demo</option><option value="api">API con datos de ejemplo</option></select></label></div>
    </header>
    <div className="global-heading"><div><p className="eyebrow">COMPRA COMPARTIDA, CONTROL INDIVIDUAL</p><h1 id="global-title">Juntos, el café cuesta menos.</h1><p className="global-subtitle">El agente compara el costo entregado. Cada negocio decide cuánto autoriza.</p></div><button className="secondary-button" onClick={() => void refresh()} disabled={loading}>{loading ? 'Comparando…' : 'Recalcular propuesta'}<ArrowRight size={16} /></button></div>
    {error && <div role="alert" className="global-error">{error}<button onClick={() => void refresh()}>Reintentar</button></div>}
    {loading ? <div className="global-empty" role="status">Comparando proveedores y calculando el reparto…</div> : !proposal ? <div className="global-empty"><UsersThree size={36} /><h2>Aún no hay una propuesta</h2><p>Calcula con faltas y ofertas de ejemplo. La API usa sus fixtures como precio individual de referencia.</p><button className="primary-button" onClick={() => changeMode('demo')}>Explorar propuesta de demo</button></div> : <>
      <div className="global-overview">
        <div className="group-card"><div className="card-caption"><UsersThree size={18} /><span>Un pedido, {ids.length} negocios</span><span className="demo-label">{provenance}</span></div><h2>Café en grano <span>250 g</span></h2><p><strong>{groupQuantity} bolsas</strong> · misma presentación, misma moneda</p><div className="price-comparison"><div><span>Comprando por separado</span><strong className="old-price" title={proposal.notes[0]}>{money(proposal.individual_total, proposal.currency)}</strong></div><ArrowRight size={24} /><div><span>En grupo · envío e IVA incluidos</span><strong>{money(proposal.total, proposal.currency)}</strong></div></div></div>
        <div className="savings-card"><span>Ahorro compartido</span><strong title={provenance}>{money(proposal.savings_total, proposal.currency)}</strong><p>{proposal.individual_total > 0 ? (proposal.savings_total / proposal.individual_total * 100).toFixed(1) : '0'}% menos · {provenance}</p><div className="savings-status"><ShieldCheck size={18} />{allApproved ? 'Demo autorizada · todavía sin pagar' : statusNames[proposal.status]}</div></div>
      </div>
      <div className="global-columns"><section className="supplier-panel" aria-labelledby="supplier-title"><div className="panel-title"><h2 id="supplier-title">Costo entregado del pedido</h2><span className="muted">{demo ? 'Comparación simulada · MXN' : 'Ofertas enviadas · demo_data'}</span></div><div className="table-scroll"><table><thead><tr><th>Proveedor</th><th>Producto</th><th>Envío + IVA</th><th>Total</th></tr></thead><tbody>{offers.map(offer => <tr key={offer.supplier} className={offer.supplier === proposal.supplier ? 'selected-offer' : ''}><th scope="row"><button className="supplier-button" disabled={!demo || loading} onClick={() => { setProposal(sampleProposal(offer)); setApproved([]); }} aria-pressed={offer.supplier === proposal.supplier}><span>{offer.supplier}</span>{offer.supplier === proposal.supplier && <CheckCircle size={16} weight="fill" />}</button><small title={offer.source}>{offer.eta_days} días · demo_data</small></th><td title={offer.source}>{money(groupQuantity * offer.unit_price)}</td><td title={offer.source}>{money(offer.shipping + offer.tax)}</td><td title={offer.source}><strong>{money(delivered(offer, groupQuantity))}</strong></td></tr>)}</tbody></table></div><p className="panel-footnote">Bolsas de 250 g. Envío e IVA se suman una vez por pedido. Ofertas simuladas; en API, el precio individual viene de fixtures del servicio.</p></section>
      <section className="allocation-panel" aria-label="Autorización por negocio">{!demo ? <PaymentControls key={proposal.id} proposal={proposal} onOrderStatus={status => setProposal(previous => previous?.id === proposal.id ? { ...previous, status } : previous)} /> : <><div className="panel-title"><h2 id="allocation-title">Cada dueño tiene la última palabra</h2><span className="muted">{approvedCount}/{ids.length} · {demo ? 'autorización simulada' : 'estado de API'}</span></div><div className="business-list">{ids.map(id => {
        const business = businesses.find(item => item.id === id);
        const rows = allocations.filter(allocation => allocation.business_id === id);
        const cost = rows.reduce((sum, row) => sum + row.cost, 0);
        const savings = rows.reduce((sum, row) => sum + row.savings, 0);
        const cap = Number(caps[id]);
        const validCap = caps[id] !== '' && Number.isFinite(cap) && cap >= cost;
        const isApproved = demo ? approved.includes(id) : rows.every(row => row.approved);
        return <div className="business-row" key={id}><div className="business-name"><strong>{business?.name ?? id}</strong><span title={provenance}>{money(cost, proposal.currency)} <small className="savings-text">ahorra {money(savings, proposal.currency)}</small></span></div><label className="budget-label">Tope MXN<input type="number" min="0" step="0.01" value={caps[id] ?? ''} onChange={event => { setCaps({ ...caps, [id]: event.target.value }); setApproved(approved.filter(item => item !== id)); }} aria-label={`Tope de ${business?.name ?? id}`} /></label><button className={`approve-button ${isApproved ? 'is-approved' : ''}`} disabled={!demo || !validCap || isApproved} onClick={() => setApproved([...approved, id])}>{isApproved ? <><CheckCircle size={16} />Autorizado</> : demo ? 'Autorizar demo' : 'No disponible'}</button>{!validCap && <small className="cap-error">El tope debe cubrir {money(cost, proposal.currency)}.</small>}</div>;
      })}</div><p className="panel-footnote">Demo vinculada a esta propuesta. Cambiar tope o proveedor reinicia la autorización. En API, usa las autorizaciones del servidor.</p></>}</section></div>
      <footer className="global-footer"><ShieldCheck size={18} /><span>{allApproved ? 'Todos autorizaron la simulación. El pago espera la integración de Reap.' : 'Ningún pago se inicia sin autorización. En API, consulta el estado devuelto por el servidor.'}</span><span className="demo-label">{provenance}</span></footer>
    </>}
  </section>;
}
