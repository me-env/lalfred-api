"""Business-level email sending.

Templates are rendered here, then handed to the provider for transport.
"""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings
from app.models import PaymentClaim, PaymentClaimType
from app.providers import resend_provider
from app.services.payment_claim_keys import format_claim_key_for_display

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


async def send_payment_claim_email(claim: PaymentClaim) -> str:
    subject = (
        "Your L'Alfred credits key"
        if claim.type == PaymentClaimType.CREDITS
        else "Your L'Alfred subscription key"
    )
    html = _env.get_template("payment_claim.html").render(
        claim_key_display=format_claim_key_for_display(claim.claim_key),
        claim_key_canonical=claim.claim_key,
        claim_type=claim.type.value,
        credits_amount=claim.credits_amount,
        support_email=settings.email_support_address,
    )
    return await resend_provider.send_email(
        to=claim.buyer_email,
        subject=subject,
        html=html,
        reply_to=settings.email_support_address,
    )
