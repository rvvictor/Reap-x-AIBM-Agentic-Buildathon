"""Verifiable purchase rules and an append-only audit log.

Checks are pure: budget cap, allowed substitutions, maximum quantity, and a
stop when the unit price moves off the authorized price. Recording a decision
adds the time and who authorized it. This module never calls Reap.
"""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CENT = Decimal("0.01")

_log: list[dict] = []


class PolicyError(ValueError):
    """A rule input is not a finite nonnegative amount."""


class PolicyRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget_cap: float = Field(ge=0)
    spent: float = Field(default=0, ge=0)
    max_qty: int = Field(gt=0)
    allowed_substitutions: list[str] = Field(default_factory=list)


class PurchaseCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    business_id: str
    sku_id: str
    qty: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    authorized_unit_price: float = Field(ge=0)
    substitution: str | None = None
    authorized_by: str = ""
    reason: str = ""


class Verdict(BaseModel):
    allowed: bool
    action: Literal["allow", "stop"]
    rule: str
    reason: str


def cents(value: float) -> Decimal:
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0:
        raise PolicyError("amount must be finite and nonnegative")
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def evaluate(rules: PolicyRules, check: PurchaseCheck) -> Verdict:
    """Return the same verdict for the same rules and check. Does not log."""

    authorizer = check.authorized_by.strip()
    if not authorizer:
        return _stop("authorization", "falta quién autoriza")

    if check.qty > rules.max_qty:
        return _stop("max_qty", f"cantidad {check.qty} supera el máximo {rules.max_qty}")

    substitution = (check.substitution or "").strip()
    if substitution:
        allowed = {item.strip().casefold() for item in rules.allowed_substitutions if item.strip()}
        if substitution.casefold() not in allowed:
            return _stop("substitution", f"sustitución {substitution} no está permitida")

    quoted = cents(check.unit_price)
    authorized = cents(check.authorized_unit_price)
    if quoted != authorized:
        return _stop(
            "price",
            f"el precio {quoted} cambió fuera de lo autorizado {authorized}",
        )

    cost = quoted * check.qty
    if cents(rules.spent) + cost > cents(rules.budget_cap):
        return _stop("budget", f"el costo {cents(rules.spent) + cost} supera el tope {cents(rules.budget_cap)}")

    reason = check.reason.strip() or "dentro del tope, la cantidad y el precio autorizado"
    return Verdict(allowed=True, action="allow", rule="ok", reason=reason)


def record(rules: PolicyRules, check: PurchaseCheck, *, at: datetime) -> dict:
    """Evaluate and append one audit entry with reason, time and authorizer."""

    if at.tzinfo is None:
        raise PolicyError("audit time must include a timezone")
    verdict = evaluate(rules, check)
    entry = {
        "id": len(_log) + 1,
        "at": at.isoformat(),
        "action": verdict.action,
        "rule": verdict.rule,
        "reason": verdict.reason,
        "authorized_by": check.authorized_by.strip(),
        "business_id": check.business_id,
        "sku_id": check.sku_id,
        "qty": check.qty,
        "unit_price": str(cents(check.unit_price)),
        "demo_data": True,
    }
    _log.append(entry)
    return entry


def audit_log() -> list[dict]:
    return list(_log)


def reset_log() -> None:
    _log.clear()


def _stop(rule: str, reason: str) -> Verdict:
    return Verdict(allowed=False, action="stop", rule=rule, reason=reason)
