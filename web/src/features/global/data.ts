export type Allocation = { business_id: string; sku_id: string; qty: number; cost: number; individual_cost: number; savings: number; approved: boolean };
export type Proposal = { id: string; category: string; supplier: string; status: 'draft' | 'pending_approval' | 'approved' | 'paid' | 'stopped' | 'failed'; total: number; individual_total: number; savings_total: number; currency: string; allocations: Allocation[]; notes: string[]; demo_data: boolean };
export type Offer = { supplier: string; unit_price: number; shipping: number; tax: number; eta_days: number; source: string };
export const businesses = [
  { id: 'cafe-aurora', name: 'Café Aurora', budget: 6000 },
  { id: 'cafe-brasa', name: 'Brasa Café', budget: 5000 },
  { id: 'cafe-cumbre', name: 'Cumbre Espresso', budget: 7000 },
  { id: 'cafe-dulce', name: 'Dulce Taza', budget: 4500 },
];
// Synthetic, comparable basket: 20 bags of coffee (250 g), MXN.
// Taxes and shipping are flat totals for the basket, added exactly once.
export const offers: Offer[] = [
  { supplier: 'Colectivo Tostador', unit_price: 190, shipping: 100, tax: 624, eta_days: 2, source: 'Fixture HACK-010 · oferta simulada' },
  { supplier: 'Origen Café', unit_price: 210, shipping: 120, tax: 691.2, eta_days: 3, source: 'Fixture HACK-010 · oferta simulada' },
  { supplier: 'Ruta del Grano', unit_price: 230, shipping: 80, tax: 748.8, eta_days: 1, source: 'Fixture HACK-010 · oferta simulada' },
];
export const quantity = 20;
export const delivered = (offer: Offer, count = quantity) => count * offer.unit_price + offer.shipping + offer.tax;
export const proposalRequest = {
  needs: businesses.map(business => ({ business_id: business.id, sku_id: `${business.id}:grano`, product_name: 'Café en grano 250 g', category: 'cafe-grano', qty: 5, needed_by: '2026-10-11', accepted_equivalents: [] })),
  offers: offers.map((offer, index) => ({ supplier: offer.supplier, product_id: `demo-coffee-${index}`, name: 'Café en grano 250 g', category: 'cafe-grano', unit_price: offer.unit_price, shipping: offer.shipping, tax: offer.tax, currency: 'MXN', eta_days: offer.eta_days, min_qty: 1, source: 'simulated', demo_data: true })),
};
export const money = (value: number, currency = 'MXN') => new Intl.NumberFormat('es-MX', { style: 'currency', currency, maximumFractionDigits: 2 }).format(value);
export function sampleProposal(offer = offers[0]): Proposal {
  const total = delivered(offer);
  const allocations = businesses.map(business => ({ business_id: business.id, sku_id: `${business.id}:grano`, qty: 5, cost: total / 4, individual_cost: 1473, savings: 1473 - total / 4, approved: false }));
  return { id: `demo-${offer.supplier}`, category: 'cafe-grano', supplier: offer.supplier, status: 'pending_approval', total, individual_total: 5892, savings_total: 5892 - total, currency: 'MXN', allocations, notes: ['Precio individual simulado: $294.60 por bolsa, entregado.', 'La comparación incluye envío e IVA; no es una cotización de Reap.'], demo_data: true };
}
const statuses = new Set(['draft', 'pending_approval', 'approved', 'paid', 'stopped', 'failed']);
const record = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value);
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value) && value >= 0;
export function parseProposals(value: unknown): Proposal[] {
  if (!Array.isArray(value)) throw new Error('La API no devolvió una lista de propuestas válida.');
  return value.map(item => {
    if (!record(item) || typeof item.id !== 'string' || typeof item.category !== 'string' || typeof item.supplier !== 'string' || typeof item.status !== 'string' || !statuses.has(item.status) || typeof item.currency !== 'string' || !/^[A-Z]{3}$/.test(item.currency) || typeof item.demo_data !== 'boolean' || !finite(item.total) || !finite(item.individual_total) || !finite(item.savings_total) || !Array.isArray(item.allocations) || !Array.isArray(item.notes) || !item.notes.every(note => typeof note === 'string')) throw new Error('La propuesta no cumple el contrato de datos.');
    for (const allocation of item.allocations) {
      if (!record(allocation) || typeof allocation.business_id !== 'string' || typeof allocation.sku_id !== 'string' || !Number.isInteger(allocation.qty) || !finite(allocation.qty) || allocation.qty === 0 || !finite(allocation.cost) || !finite(allocation.individual_cost) || !finite(allocation.savings) || typeof allocation.approved !== 'boolean' || Math.abs(allocation.individual_cost - allocation.cost - allocation.savings) > 0.02) throw new Error('El reparto contiene datos inválidos o un negocio sin ahorro.');
    }
    const allocations = item.allocations as Allocation[];
    if (Math.abs(allocations.reduce((sum, allocation) => sum + allocation.cost, 0) - item.total) > 0.02 || Math.abs(allocations.reduce((sum, allocation) => sum + allocation.individual_cost, 0) - item.individual_total) > 0.02 || Math.abs(allocations.reduce((sum, allocation) => sum + allocation.savings, 0) - item.savings_total) > 0.02 || Math.abs(item.individual_total - item.total - item.savings_total) > 0.02) throw new Error('Los totales no coinciden con el reparto.');
    return item as Proposal;
  });
}
export function parseRequestedProposals(value: unknown): Proposal[] {
  const results = parseProposals(value);
  if (results.length > 1 || results.some(result => result.category !== 'cafe-grano' || !result.demo_data || result.currency !== 'MXN')) throw new Error('La respuesta no corresponde al pedido de ejemplo. Se detuvo la propuesta.');
  for (const result of results) {
    const offer = offers.find(item => item.supplier === result.supplier);
    const count = result.allocations.reduce((sum, row) => sum + row.qty, 0);
    const changedQuantity = result.allocations.some(row => {
      const need = proposalRequest.needs.find(item => item.business_id === row.business_id && item.sku_id === row.sku_id);
      const allocated = result.allocations.filter(item => item.business_id === row.business_id && item.sku_id === row.sku_id).reduce((sum, item) => sum + item.qty, 0);
      return !need || allocated > need.qty;
    });
    if (!offer || Math.abs(delivered(offer, count) - result.total) > 0.02 || changedQuantity) throw new Error('El proveedor, el precio o las cantidades cambiaron. Se detuvo la propuesta.');
  }
  return results;
}
