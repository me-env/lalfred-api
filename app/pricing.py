"""
Credit pricing system.

1 credit = $0.0001 USD (0.1 milli-dollar).
Margin is taken at purchase time (via CREDITS_AWARDED_PER_DOLLAR_SPENT).
Usage deductions reflect raw provider cost — no markup at request time.
"""

from dataclasses import dataclass
from math import ceil

CREDIT_VALUE_USD = 0.0001

# Purchase conversion: credits awarded per $1 of product price.
# Lower = higher margin. At 5000, margin is ~50% of product price.
CREDITS_AWARDED_PER_DOLLAR_SPENT = 5000
PRICING_USD_PER_EUR = 1.08

PREFLIGHT_DURATION_THRESHOLD_S = 300  # 5 minutes
MAX_NEGATIVE_BALANCE = -500


# ---------------------------------------------------------------------------
# Provider model costs (USD)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class STTProviderModel:
    model: str
    cost_per_second_usd: float
    keyterms_surcharge_per_second_usd: float = 0.0


@dataclass(frozen=True)
class LLMProviderModel:
    model: str
    input_cost_per_token_usd: float
    output_cost_per_token_usd: float


STT_MODELS: dict[str, STTProviderModel] = {
    "scribe_v2": STTProviderModel(
        model="scribe_v2",
        cost_per_second_usd=0.22 / 3600,  # $0.22/hour
        keyterms_surcharge_per_second_usd=0.05 / 3600,  # $0.05/hour
    ),
}

LLM_MODELS: dict[str, LLMProviderModel] = {
    "gpt-4.1": LLMProviderModel(
        model="gpt-4.1",
        input_cost_per_token_usd=2.00 / 1_000_000,   # $2.00 / 1M input tokens
        output_cost_per_token_usd=8.00 / 1_000_000,   # $8.00 / 1M output tokens
    ),
    "gpt-4.1-mini": LLMProviderModel(
        model="gpt-4.1-mini",
        input_cost_per_token_usd=0.40 / 1_000_000,    # $0.40 / 1M input tokens
        output_cost_per_token_usd=1.60 / 1_000_000,   # $1.60 / 1M output tokens
    ),
}


# ---------------------------------------------------------------------------
# LemonSqueezy product catalog
# Keyed by LS variant ID — update these when products are created in the
# LS dashboard.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Product:
    name: str
    type: str  # "credits" | "byok"


PRODUCTS_BY_VARIANT_ID: dict[str, Product] = {
    "1604360": Product(name="credits", type="credits"),
    "1604374": Product(name="byok_monthly", type="byok"),
    "1604369": Product(name="byok_annual", type="byok"),
}


def resolve_product(variant_id: str | None) -> Product | None:
    if variant_id and variant_id in PRODUCTS_BY_VARIANT_ID:
        return PRODUCTS_BY_VARIANT_ID[variant_id]
    return None


def credits_from_payment(cents: int, currency: str) -> int:
    """
    Convert a payment amount in cents to credit count.

    `currency` is ISO-like (e.g. "USD", "EUR").
    """
    currency_code = currency.upper()
    if currency_code == "USD":
        usd_cents = cents
    elif currency_code == "EUR":
        usd_cents = int(round(cents * PRICING_USD_PER_EUR))
    else:
        raise ValueError(f"Unsupported currency: {currency}")
    return usd_cents * CREDITS_AWARDED_PER_DOLLAR_SPENT // 100


# ---------------------------------------------------------------------------
# Credit cost calculators
# ---------------------------------------------------------------------------

def stt_credits(
    duration_seconds: float, model: str = "scribe_v2", *, keyterms: bool = False,
) -> int:
    """Credits to deduct for a speech-to-text request."""
    m = STT_MODELS[model]
    cost_usd = duration_seconds * m.cost_per_second_usd
    if keyterms:
        cost_usd += duration_seconds * m.keyterms_surcharge_per_second_usd
    return max(1, ceil(cost_usd / CREDIT_VALUE_USD))


def llm_credits(input_tokens: int, output_tokens: int, model: str) -> int:
    """Credits to deduct for an LLM request."""
    m = LLM_MODELS[model]
    cost_usd = input_tokens * m.input_cost_per_token_usd + output_tokens * m.output_cost_per_token_usd
    return max(1, ceil(cost_usd / CREDIT_VALUE_USD))


def estimate_stt_credits(
    duration_seconds: float, model: str = "scribe_v2", *, keyterms: bool = False,
) -> int:
    """Pre-flight estimate (same formula, used before the call)."""
    return stt_credits(duration_seconds, model, keyterms=keyterms)
