import logging

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from app.config import settings
from app.schemas.releases import ReleaseManifest

logger = logging.getLogger(__name__)


async def fetch_latest_manifest() -> ReleaseManifest:
    """Fetch and validate `latest.json` from the release bucket.

    Raises HTTPException(502) when the bucket is unreachable, returns a
    non-200, or returns JSON that doesn't conform to `ReleaseManifest` —
    all three failure modes are surfaced as the same upstream-broken
    signal rather than letting them mask each other downstream.
    """
    url = f"{settings.release_bucket_url}/latest.json"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"Accept": "application/json"})
    except httpx.HTTPError as exc:
        logger.error("release manifest fetch failed url=%s err=%s", url, exc)
        raise HTTPException(status_code=502, detail="Release manifest unavailable") from exc

    if resp.status_code != 200:
        logger.error(
            "release manifest unavailable url=%s status=%d", url, resp.status_code
        )
        raise HTTPException(status_code=502, detail="Release manifest unavailable")

    try:
        return ReleaseManifest.model_validate_json(resp.content)
    except ValidationError as exc:
        logger.error("release manifest invalid url=%s err=%s", url, exc)
        raise HTTPException(status_code=502, detail="Release manifest invalid") from exc
