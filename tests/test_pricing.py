from app.pricing import (PRODUCTS_BY_VARIANT_ID, Product, credits_from_payment,
                         estimate_stt_credits, llm_credits, resolve_product,
                         stt_credits)


def test_stt_credits_short():
    assert stt_credits(1.0) == 1  # 1s → minimal cost, floor at 1


def test_stt_credits_one_minute():
    credits = stt_credits(60.0)
    assert credits == 37  # 60 * 0.611 = 36.67 → ceil = 37


def test_stt_credits_one_hour():
    credits = stt_credits(3600.0)
    assert credits == 2200  # 3600 * 0.611 = 2200.0


def test_stt_credits_five_minutes():
    credits = stt_credits(300.0)
    assert credits == 184  # 300 * 0.611 = 183.33 → ceil = 184


def test_estimate_equals_actual():
    assert estimate_stt_credits(120.0) == stt_credits(120.0)


def test_llm_credits_gpt41():
    credits = llm_credits(input_tokens=1000, output_tokens=500, model="gpt-4.1")
    # 1000 * 2e-6 + 500 * 8e-6 = 0.002 + 0.004 = 0.006 → 60 credits
    assert credits == 60


def test_llm_credits_gpt41_mini():
    credits = llm_credits(input_tokens=1000, output_tokens=500, model="gpt-4.1-mini")
    # 1000 * 4e-7 + 500 * 1.6e-6 = 0.0004 + 0.0008 = 0.0012 → ceil = 12
    assert credits == 12


def test_llm_credits_minimum_one():
    credits = llm_credits(input_tokens=10, output_tokens=5, model="gpt-4.1-mini")
    assert credits == 1


def test_credits_from_payment_usd():
    assert credits_from_payment(1760, "USD") == 88000  # $17.60 → 88000 credits
    assert credits_from_payment(400, "USD") == 20000    # $4.00 → 20000 credits
    assert credits_from_payment(1000, "USD") == 50000   # $10.00 → 50000 credits


def test_credits_from_payment_eur():
    assert credits_from_payment(465, "EUR") == 25100  # €4.65 @ 1.08 = $5.02 -> 25100 credits


def test_resolve_product_credits():
    product = resolve_product("1604360")
    assert product is not None
    assert product.type == "credits"


def test_resolve_product_byok():
    product = resolve_product("1604374")
    assert product is not None
    assert product.type == "byok"


def test_resolve_product_unknown_variant_id():
    product = resolve_product("unknown-variant")
    assert product is None
