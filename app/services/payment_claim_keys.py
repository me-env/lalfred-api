"""Pure helpers for payment-claim key generation and formatting.

Lives in its own module so it can be imported by both
``payment_claim_service`` and ``email_service`` without creating a cycle.

Canonical form is what we store in the DB and accept on the wire:
16 uppercase characters from a human-friendly alphabet, no separators.
The dashed ``XXXX-XXXX-XXXX-XXXX`` form is purely presentational.
"""
import secrets

# Avoid ambiguous chars (0/O/1/I/L) for keys typed by humans.
_KEY_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_KEY_GROUP_LEN = 4
_KEY_GROUPS = 4
_KEY_LEN = _KEY_GROUP_LEN * _KEY_GROUPS


def generate_claim_key() -> str:
    """Generate a canonical (no-dash, uppercase) claim key."""
    return "".join(secrets.choice(_KEY_ALPHABET) for _ in range(_KEY_LEN))


def normalize_claim_key(raw: str) -> str:
    """Reduce any user-typed/pasted key to its canonical form.

    Accepts dashed (``XXXX-XXXX-XXXX-XXXX``) or undashed input, mixed case,
    and surrounding whitespace. The DB stores and looks up only canonical keys.
    """
    return raw.strip().replace("-", "").replace(" ", "").upper()


def format_claim_key_for_display(canonical: str) -> str:
    """Insert dashes every 4 chars for human-readable presentation."""
    return "-".join(
        canonical[i : i + _KEY_GROUP_LEN]
        for i in range(0, len(canonical), _KEY_GROUP_LEN)
    )
