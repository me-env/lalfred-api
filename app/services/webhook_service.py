import logging
from calendar import monthrange
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.pricing import credits_from_payment, resolve_product
from app.providers import lemonsqueezy_provider
from app.schemas.webhooks import (
    LemonSqueezyOrderCreatedAttributes, LemonSqueezyOrderCreatedWebhook,
    LemonSqueezySubscriptionPaymentSuccessAttributes,
    LemonSqueezySubscriptionPaymentSuccessWebhook, LemonSqueezyWebhookResponse)
from app.services import payment_claim_service

logger = logging.getLogger(__name__)


async def handle_order_created_webhook(
    db: AsyncSession,
    payload: bytes,
    signature: str,
    data: LemonSqueezyOrderCreatedWebhook,
) -> LemonSqueezyWebhookResponse:
    _verify_signature(payload, signature)
    attributes = data.data.attributes
    order_id = str(data.data.id)
    variant_id = str(attributes.first_order_item.variant_id)
    logger.info(
        "order_created: signature ok, order_id=%s variant_id=%s test_mode=%s",
        order_id, variant_id, data.meta.test_mode,
    )

    product = resolve_product(variant_id)
    if product is None:
        logger.critical("order_created: unknown variant_id=%s order_id=%s", variant_id, order_id)
        return LemonSqueezyWebhookResponse(status="unknown_product")

    if product.type != "credits":
        # NOTE: order_created for Subscription is ignored in favor of subscription_payment_success
        logger.info(
            "order_created: ignored (subscriptions use subscription_payment_success): order_id=%s variant_id=%s product_type=%s",
            order_id, variant_id, product.type,
        )
        return LemonSqueezyWebhookResponse(status="ignored")

    payment_cents, payment_currency = _resolve_payment_amount(attributes)
    if payment_cents is None or payment_currency is None:
        logger.error("order_created: missing payment amount order_id=%s", order_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing payment amount")

    credits = credits_from_payment(payment_cents, payment_currency)
    claim = await payment_claim_service.create_credit_claim(
        db,
        buyer_email=attributes.user_email,
        lemon_order_id=order_id,
        credits_amount=credits,
    )
    if claim is None:
        return LemonSqueezyWebhookResponse(status="already_processed")

    return LemonSqueezyWebhookResponse(status="ok", credits_added=credits, id=claim.id)


async def handle_subscription_payment_success_webhook(
    db: AsyncSession,
    payload: bytes,
    signature: str,
    data: LemonSqueezySubscriptionPaymentSuccessWebhook,
) -> LemonSqueezyWebhookResponse:
    _verify_signature(payload, signature)
    attributes = data.data.attributes
    invoice_id = data.data.id
    subscription_id = attributes.subscription_id
    logger.info(
        "subscription_payment_success: signature ok, invoice_id=%s subscription_id=%s variant_id=%s test_mode=%s billing_reason=%s",
        invoice_id, subscription_id, attributes.variant_id,
        data.meta.test_mode, attributes.billing_reason,
    )

    starts_at, ends_at = _resolve_subscription_window(attributes)
    claim = await payment_claim_service.create_subscription_claim(
        db,
        buyer_email=attributes.user_email,
        lemon_invoice_id=invoice_id,
        lemon_subscription_id=str(subscription_id),
        starts_at=starts_at,
        ends_at=ends_at,
    )
    if claim is None:
        return LemonSqueezyWebhookResponse(status="already_processed")

    return LemonSqueezyWebhookResponse(status="ok", id=claim.id)


def _verify_signature(payload: bytes, signature: str) -> None:
    if not lemonsqueezy_provider.verify_signature(payload, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")


def _resolve_subscription_window(
    attributes: LemonSqueezySubscriptionPaymentSuccessAttributes,
) -> tuple[datetime, datetime]:
    starts_at = attributes.created_at.astimezone(UTC) if attributes.created_at else datetime.now(UTC)
    ends_at = attributes.ends_at.astimezone(UTC) if attributes.ends_at else _infer_subscription_end(starts_at, attributes.variant_id)
    if ends_at <= starts_at:
        ends_at = _infer_subscription_end(starts_at, attributes.variant_id)
    return starts_at, ends_at


def _infer_subscription_end(starts_at: datetime, variant_id: int | None) -> datetime:
    product = resolve_product(str(variant_id)) if variant_id is not None else None
    if product and product.name == "byok_annual":
        return _add_years(starts_at, years=1)
    return _add_months(starts_at, months=1)


def _add_months(dt: datetime, *, months: int) -> datetime:
    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _add_years(dt: datetime, *, years: int) -> datetime:
    year = dt.year + years
    day = min(dt.day, monthrange(year, dt.month)[1])
    return dt.replace(year=year, day=day)


def _resolve_payment_amount(attributes: LemonSqueezyOrderCreatedAttributes) -> tuple[int | None, str | None]:
    if attributes.subtotal is not None and attributes.currency is not None:
        return attributes.subtotal, attributes.currency
    if attributes.total is not None and attributes.currency is not None:
        return attributes.total, attributes.currency
    if attributes.subtotal_usd is not None:
        return attributes.subtotal_usd, "USD"
    return None, None
