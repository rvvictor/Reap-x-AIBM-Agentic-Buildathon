from decimal import DecimalException

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from app.config import settings
from app.schemas import Business, Need, Product, Proposal, SupplierOffer
from app.schemas.loader import load_products
from app.services.global_agent import demo_offers, generate_proposals, proposal_store

router = APIRouter(prefix="/api/global", tags=["global"])


@router.get("/proposals/{proposal_id}", response_model=Proposal)
def get_proposal(proposal_id: str) -> Proposal:
    if not settings.demo_mode:
        raise HTTPException(422, "Demo proposal store is unavailable outside DEMO_MODE")
    proposal = proposal_store.get(proposal_id)
    if proposal is None:
        raise HTTPException(404, "Proposal not found")
    return proposal


class ProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    needs: list[Need]
    products: list[Product] | None = None
    offers: list[SupplierOffer] | None = None
    businesses: list[Business] | None = None


@router.post("/proposals", response_model=list[Proposal])
def proposals(request: ProposalRequest) -> list[Proposal]:
    # Caller prices are demonstration input, never authoritative for checkout.
    if not settings.demo_mode:
        raise HTTPException(
            422,
            "Caller-supplied draft pricing is available only in DEMO_MODE; live offers require server-side Reap quotes",
        )
    products = request.products if request.products is not None else load_products()
    try:
        offers = request.offers if request.offers is not None else demo_offers(products)
        generated = generate_proposals(
            request.needs, products, offers, businesses=request.businesses
        )
    except (ValueError, OverflowError, DecimalException) as error:
        raise HTTPException(422, str(error)) from error
    for proposal in generated:
        proposal.demo_data = True
        proposal.notes.append(
            "Caller/fixture draft pricing is simulated and must not authorize checkout."
        )
    # Demo-only process-local store; restart clears drafts. Replay preserves approvals.
    return [proposal_store.setdefault(p.id, p) for p in generated]


@router.get("/proposals", response_model=list[Proposal])
def list_proposals() -> list[Proposal]:
    if not settings.demo_mode:
        raise HTTPException(422, "Demo proposal store is unavailable outside DEMO_MODE")
    return [proposal_store[key] for key in sorted(proposal_store)]
