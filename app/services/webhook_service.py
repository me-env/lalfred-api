import logging
from calendar import monthrange
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SubscriptionPayment, TransactionType
from app.pricing import credits_from_payment, resolve_product
from app.providers import lemonsqueezy_provider
from app.repositories import (credit_repository, subscription_repository,
                              user_repository)
from app.schemas.webhooks import (
    LemonSqueezyOrderCreatedAttributes, LemonSqueezyOrderCreatedWebhook,
    LemonSqueezySubscriptionPaymentSuccessAttributes,
    LemonSqueezySubscriptionPaymentSuccessWebhook, LemonSqueezyWebhookResponse)

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
        order_id,
        variant_id,
        data.meta.test_mode,
    )

    product = resolve_product(variant_id)
    if product is None:
        logger.critical("order_created: unknown variant_id=%s order_id=%s", variant_id, order_id)
        return LemonSqueezyWebhookResponse(status="unknown_product")

    if product.type != "credits":
        # NOTE: order_created for Subscription are ignored in favor of subscription_payment_success
        logger.info(
            "order_created: ignored (subscriptions use subscription_payment_success): order_id=%s variant_id=%s product_type=%s",
            order_id,
            variant_id,
            product.type,
        )
        return LemonSqueezyWebhookResponse(status="ignored")

    payment_cents, payment_currency = _resolve_payment_amount(attributes)
    if payment_cents is None or payment_currency is None:
        logger.error("order_created: missing payment amount order_id=%s", order_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing payment amount")

    user = await _require_user_by_email(db, attributes.user_email, order_id)
    logger.info("order_created: resolved user id=%s email=%s", user.id, user.email)

    existing = await credit_repository.find_by_order_id(db, order_id)
    if existing is not None:
        logger.info("order_created: already_processed order_id=%s credit_id=%s", order_id, existing.id)
        return LemonSqueezyWebhookResponse(status="already_processed")

    credits = credits_from_payment(payment_cents, payment_currency)
    user.credits += credits
    credit = await credit_repository.create(
        db,
        user_id=user.id,
        amount=credits,
        type=TransactionType.PURCHASE,
        description=f"Purchased {credits} credits",
        lemon_order_id=order_id,
    )
    logger.info(
        "order_created: added %s credits to user id=%s order_id=%s credit_row_id=%s",
        credits,
        user.id,
        order_id,
        credit.id,
    )
    return LemonSqueezyWebhookResponse(status="ok", credits_added=credits, id=credit.id)


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
        invoice_id,
        subscription_id,
        attributes.variant_id,
        data.meta.test_mode,
        attributes.billing_reason,
    )

    user = await _require_user_by_email(db, attributes.user_email, invoice_id)
    logger.info(
        "subscription_payment_success: resolved user id=%s email=%s invoice_id=%s",
        user.id,
        user.email,
        invoice_id,
    )
    existing = await subscription_repository.find_by_invoice_id(db, invoice_id)
    if existing is not None:
        logger.info(
            "subscription_payment_success: already_processed invoice_id=%s subscription_payment_id=%s",
            invoice_id,
            existing.id,
        )
        return LemonSqueezyWebhookResponse(status="already_processed")

    starts_at, ends_at = _resolve_subscription_window(attributes)
    logger.info(
        "subscription_payment_success: recording payment user_id=%s window=%s -> %s",
        user.id,
        starts_at.isoformat(),
        ends_at.isoformat(),
    )
    subscription: SubscriptionPayment = await subscription_repository.create(
        db,
        user_id=user.id,
        lemon_subscription_id=str(subscription_id),
        lemon_invoice_id=invoice_id,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    logger.info(
        "subscription_payment_success: stored subscription_payment id=%s user_id=%s lemon_subscription_id=%s invoice_id=%s period=%s -> %s",
        subscription.id,
        user.id,
        subscription_id,
        invoice_id,
        starts_at.isoformat(),
        ends_at.isoformat(),
    )
    return LemonSqueezyWebhookResponse(status="ok")


def _verify_signature(payload: bytes, signature: str) -> None:
    if not lemonsqueezy_provider.verify_signature(payload, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")


async def _require_user_by_email(db: AsyncSession, email: str, webhook_id: str):
    user = await user_repository.find_by_email(db, email)
    if user is None:
        logger.warning("Webhook %s for unknown user email: %s", webhook_id, email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


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
