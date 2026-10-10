import { useRef, useState } from 'react';
import { ArrowRight, CheckCircle, Coffee, ShieldCheck, UsersThree } from '@phosphor-icons/react';
import { businesses, delivered, money, offers, quantity, sampleProposal, type Proposal } from './data';
import './global.css';

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

  function changeMode(next: 'demo' | 'api') {
    refreshVersion.current += 1;
    setMode(next); setLoading(false); setApproved([]); setError(''); setProposal(next === 'demo' ? sampleProposal() : null);
  }
  async function refresh() {
    const version = ++refreshVersion.current;
    setLoading(true); setError(''); setApproved([]);
    try {
      if (mode === 'api') throw new Error('La conexión espera el servicio de propuestas. Puedes explorar la demo mientras se integra.');
      await new Promise(resolve => setTimeout(resolve, 150));
      if (version === refreshVersion.current) setProposal(sampleProposal());
    } catch (cause) { if (version === refreshVersion.current) setError(cause instanceof Error ? cause.message : 'No se pudo recuperar la propuesta.'); }
    finally { if (version === refreshVersion.current) setLoading(false); }
  }
  const allocations = proposal?.allocations ?? [];
  const ids = [...new Set(allocations.map(allocation => allocation.business_id))];
  const allApproved = ids.length > 0 && ids.every(id => approved.includes(id));
  const demo = mode === 'demo';
  const provenance = proposal?.demo_data ? 'demo_data · cifras simuladas' : 'Fuente: API de propuestas';

  return <section className="bodega-global" aria-labelledby="global-title">
    <header className="global-header">
      <div className="global-brand"><Coffee size={24} weight="duotone" /><strong>Bodega</strong><span>/ Agente global</span></div>
      <div className="global-controls"><span className="demo-label">{demo ? 'demo_data · simulación' : 'Conexión API'}</span><label className="mode-label">Datos<select value={mode} onChange={event => changeMode(event.target.value as 'demo' | 'api')}><option value="demo">Demo</option><option value="api">API</option></select></label></div>
    </header>
    <div className="global-heading"><div><p className="eyebrow">COMPRA COMPARTIDA, CONTROL INDIVIDUAL</p><h1 id="global-title">Juntos, el café cuesta menos.</h1><p className="global-subtitle">El agente compara el costo entregado. Cada negocio decide cuánto autoriza.</p></div><button className="secondary-button" onClick={() => void refresh()} disabled={loading}>{loading ? 'Comparando…' : 'Recalcular propuesta'}<ArrowRight size={16} /></button></div>
    {error && <div role="alert" className="global-error">{error}<button onClick={() => void refresh()}>Reintentar</button></div>}
    {loading ? <div className="global-empty" role="status">Comparando proveedores y calculando el reparto…</div> : !proposal ? <div className="global-empty"><UsersThree size={36} /><h2>Aún no hay una propuesta conectada</h2><p>Los datos de la API aparecerán aquí cuando el agente global esté disponible.</p><button className="primary-button" onClick={() => changeMode('demo')}>Explorar propuesta de demo</button></div> : <>
      <div className="global-overview">
        <div className="group-card"><div className="card-caption"><UsersThree size={18} /><span>Un pedido, cuatro negocios</span><span className="demo-label">{provenance}</span></div><h2>Café en grano <span>250 g</span></h2><p><strong>{quantity} bolsas</strong> · misma presentación, misma moneda</p><div className="price-comparison"><div><span>Comprando por separado</span><strong className="old-price" title={proposal.notes[0]}>{money(proposal.individual_total, proposal.currency)}</strong></div><ArrowRight size={24} /><div><span>En grupo · envío e IVA incluidos</span><strong>{money(proposal.total, proposal.currency)}</strong></div></div></div>
        <div className="savings-card"><span>Ahorro compartido</span><strong title={provenance}>{money(proposal.savings_total, proposal.currency)}</strong><p>{proposal.individual_total > 0 ? (proposal.savings_total / proposal.individual_total * 100).toFixed(1) : '0'}% menos · {provenance}</p><div className="savings-status"><ShieldCheck size={18} />{allApproved ? 'Demo autorizada · todavía sin pagar' : statusNames[proposal.status]}</div></div>
      </div>
      <div className="global-columns"><section className="supplier-panel" aria-labelledby="supplier-title"><div className="panel-title"><h2 id="supplier-title">Costo real del pedido</h2><span className="muted">{demo ? 'Comparación simulada · MXN' : 'Fuente: API'}</span></div><div className="table-scroll"><table><thead><tr><th>Proveedor</th><th>Producto</th><th>Envío + IVA</th><th>Total</th></tr></thead><tbody>{offers.map(offer => <tr key={offer.supplier} className={offer.supplier === proposal.supplier ? 'selected-offer' : ''}><th scope="row"><button className="supplier-button" disabled={!demo || loading} onClick={() => { setProposal(sampleProposal(offer)); setApproved([]); }} aria-pressed={offer.supplier === proposal.supplier}><span>{offer.supplier}</span>{offer.supplier === proposal.supplier && <CheckCircle size={16} weight="fill" />}</button><small title={offer.source}>{offer.eta_days} días · demo_data</small></th><td title={offer.source}>{money(quantity * offer.unit_price)}</td><td title={offer.source}>{money(offer.shipping + offer.tax)}</td><td title={offer.source}><strong>{money(delivered(offer))}</strong></td></tr>)}</tbody></table></div><p className="panel-footnote">20 bolsas de 250 g. Envío e IVA se suman una vez por pedido. Ofertas simuladas, sin cotización de Reap.</p></section>
      <section className="allocation-panel" aria-labelledby="allocation-title"><div className="panel-title"><h2 id="allocation-title">Cada dueño tiene la última palabra</h2><span className="muted">{approved.length}/{ids.length} · autorización simulada</span></div><div className="business-list">{ids.map(id => {
        const business = businesses.find(item => item.id === id);
        const rows = allocations.filter(allocation => allocation.business_id === id);
        const cost = rows.reduce((sum, row) => sum + row.cost, 0);
        const savings = rows.reduce((sum, row) => sum + row.savings, 0);
        const cap = Number(caps[id]);
        const validCap = caps[id] !== '' && Number.isFinite(cap) && cap >= cost;
        const isApproved = approved.includes(id);
        return <div className="business-row" key={id}><div className="business-name"><strong>{business?.name ?? id}</strong><span title={provenance}>{money(cost, proposal.currency)} <small className="savings-text">ahorra {money(savings, proposal.currency)}</small></span></div><label className="budget-label">Tope MXN<input type="number" min="0" step="0.01" value={caps[id] ?? ''} onChange={event => { setCaps({ ...caps, [id]: event.target.value }); setApproved(approved.filter(item => item !== id)); }} aria-label={`Tope de ${business?.name ?? id}`} /></label><button className={`approve-button ${isApproved ? 'is-approved' : ''}`} disabled={!demo || !validCap || isApproved} onClick={() => setApproved([...approved, id])}>{isApproved ? <><CheckCircle size={16} />Autorizado</> : 'Autorizar demo'}</button>{!validCap && <small className="cap-error">El tope debe cubrir {money(cost, proposal.currency)}.</small>}</div>;
      })}</div><p className="panel-footnote">Autorizaciones de demo ligadas a esta propuesta. Cambiar proveedor o tope pide autorización otra vez.</p></section></div>
      <footer className="global-footer"><ShieldCheck size={18} /><span>{allApproved ? 'Todos autorizaron la simulación. El pago espera la integración de Reap.' : 'Ningún pago se inicia sin autorización. Los pedidos confirmados aparecerán tras integrar pagos.'}</span><span className="demo-label">{provenance}</span></footer>
    </>}
  </section>;
}
