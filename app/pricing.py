"""
Credit pricing system.

1 credit = $0.001 USD (1 milli-dollar).
Margin is taken at purchase time (via CREDITS_PER_USD).
Usage deductions reflect raw provider cost — no markup at request time.
"""

from dataclasses import dataclass
from math import ceil

CREDIT_VALUE_USD = 0.001

# Purchase conversion: credits awarded per $1 of product price.
# Lower = higher margin. At 500, margin is ~50% of product price.
CREDITS_PER_USD = 500

PREFLIGHT_DURATION_THRESHOLD_S = 300  # 5 minutes
MAX_NEGATIVE_BALANCE = -50


# ---------------------------------------------------------------------------
# Provider model costs (USD)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProviderModel:
    provider: str
    model: str
    unit: str
    cost_usd: float


ELEVENLABS_MODELS: dict[str, ProviderModel] = {
    "scribe_v2": ProviderModel(
        provider="elevenlabs",
        model="scribe_v2",
        unit="second",
        cost_usd=0.22 / 3600,  # $0.22/hour
    ),
}

OPENAI_MODELS: dict[str, ProviderModel] = {
    "gpt-4.1": ProviderModel(
        provider="openai",
        model="gpt-4.1",
        unit="token",
        cost_usd=0.0,  # placeholder — split into input/output below
    ),
    "gpt-4.1-mini": ProviderModel(
        provider="openai",
        model="gpt-4.1-mini",
        unit="token",
        cost_usd=0.0,
    ),
}

# OpenAI per-token costs (USD) — separate input/output rates
OPENAI_TOKEN_COSTS: dict[str, dict[str, float]] = {
    "gpt-4.1": {
        "input": 2.00 / 1_000_000,   # $2.00 / 1M input tokens
        "output": 8.00 / 1_000_000,   # $8.00 / 1M output tokens
    },
    "gpt-4.1-mini": {
        "input": 0.40 / 1_000_000,    # $0.40 / 1M input tokens
        "output": 1.60 / 1_000_000,   # $1.60 / 1M output tokens
    },
}


# ---------------------------------------------------------------------------
# LemonSqueezy product catalog
# Keyed by LS variant ID — update these when products are created in the
# LS dashboard. Falls back to variant_name/product_name lookup.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Product:
    name: str
    price_usd: int  # cents
    credits: int


PRODUCTS_BY_VARIANT_ID: dict[str, Product] = {
    # "123456": Product(name="starter", price_usd=500, credits=2500),
}

PRODUCTS_BY_NAME: dict[str, Product] = {
    "starter": Product(name="starter", price_usd=500, credits=2500),
    "pro": Product(name="pro", price_usd=2000, credits=10_000),
    "unlimited": Product(name="unlimited", price_usd=5000, credits=25_000),
}


def resolve_product(variant_id: str | None, variant_name: str, product_name: str) -> Product | None:
    if variant_id and variant_id in PRODUCTS_BY_VARIANT_ID:
        return PRODUCTS_BY_VARIANT_ID[variant_id]
    return PRODUCTS_BY_NAME.get(variant_name) or PRODUCTS_BY_NAME.get(product_name)


# ---------------------------------------------------------------------------
# Credit cost calculators
# ---------------------------------------------------------------------------

def stt_credits(duration_seconds: float, model: str = "scribe_v2") -> int:
    """Credits to deduct for a speech-to-text request."""
    model_info = ELEVENLABS_MODELS[model]
    cost_usd = duration_seconds * model_info.cost_usd
    return max(1, ceil(cost_usd / CREDIT_VALUE_USD))


def llm_credits(input_tokens: int, output_tokens: int, model: str) -> int:
    """Credits to deduct for an LLM request."""
    rates = OPENAI_TOKEN_COSTS[model]
    cost_usd = input_tokens * rates["input"] + output_tokens * rates["output"]
    return max(1, ceil(cost_usd / CREDIT_VALUE_USD))


def estimate_stt_credits(duration_seconds: float, model: str = "scribe_v2") -> int:
    """Pre-flight estimate (same formula, used before the call)."""
    return stt_credits(duration_seconds, model)
