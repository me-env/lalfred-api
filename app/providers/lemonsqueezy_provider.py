import hashlib
import hmac

from app.config import settings


def verify_signature(payload: bytes, signature: str) -> bool:
    digest = hmac.new(
        settings.lemonsqueezy_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature)
