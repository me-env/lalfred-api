from app.pricing import (PRODUCTS_BY_NAME, estimate_stt_credits, llm_credits,
                         resolve_product, stt_credits)


def test_stt_credits_short():
    assert stt_credits(1.0) == 1  # 1s → minimal cost, floor at 1


def test_stt_credits_one_minute():
    credits = stt_credits(60.0)
    assert credits == 4  # 60 * 0.0611 = 3.67 → ceil = 4


def test_stt_credits_one_hour():
    credits = stt_credits(3600.0)
    assert credits == 220  # 3600 * 0.0611 = 220.0


def test_stt_credits_five_minutes():
    credits = stt_credits(300.0)
    assert credits == 19  # 300 * 0.0611 = 18.33 → ceil = 19


def test_estimate_equals_actual():
    assert estimate_stt_credits(120.0) == stt_credits(120.0)


def test_llm_credits_gpt41():
    credits = llm_credits(input_tokens=1000, output_tokens=500, model="gpt-4.1")
    # 1000 * 2e-6 + 500 * 8e-6 = 0.002 + 0.004 = 0.006 → 6 credits
    assert credits == 6


def test_llm_credits_gpt41_mini():
    credits = llm_credits(input_tokens=1000, output_tokens=500, model="gpt-4.1-mini")
    # 1000 * 4e-7 + 500 * 1.6e-6 = 0.0004 + 0.0008 = 0.0012 → ceil = 2
    assert credits == 2


def test_llm_credits_minimum_one():
    credits = llm_credits(input_tokens=10, output_tokens=5, model="gpt-4.1-mini")
    assert credits == 1


def test_resolve_product_by_name():
    product = resolve_product(None, "starter", "")
    assert product is not None
    assert product.credits == PRODUCTS_BY_NAME["starter"].credits


def test_resolve_product_by_product_name_fallback():
    product = resolve_product(None, "unknown", "pro")
    assert product is not None
    assert product.credits == PRODUCTS_BY_NAME["pro"].credits


def test_resolve_product_unknown():
    product = resolve_product(None, "unknown", "unknown")
    assert product is None
