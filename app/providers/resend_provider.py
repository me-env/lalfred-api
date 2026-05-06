"""Thin transport wrapper around the Resend SDK.

This module knows nothing about business logic. It just forwards
content to Resend's API and returns the resulting email id.
"""
import logging

import resend

from app.config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.resend_api_key


async def send_email(
    *,
    to: str | list[str],
    subject: str,
    html: str,
    from_address: str | None = None,
    reply_to: str | None = None,
) -> str:
    params: resend.Emails.SendParams = {
        "from": from_address or settings.email_from_address,
        "to": to,
        "subject": subject,
        "html": html,
    }
    if reply_to is not None:
        params["reply_to"] = reply_to

    response = await resend.Emails.send_async(params)
    email_id = response["id"]
    logger.info("resend: email sent id=%s subject=%r to=%s", email_id, subject, to)
    return email_id
