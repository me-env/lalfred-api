import logging
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.config import settings
from app.providers import releases_provider
from app.schemas.releases import ReleaseManifest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/releases", tags=["releases"])

# The `[file]` segment is user-controlled, so we validate against an allowlist
# to prevent the route being turned into an open redirector. The character
# class is intentionally permissive (alphanumerics, dot, plus, hyphen,
# underscore) so prerelease / build-suffix versions like `1.2.0-beta.3` or
# `1.2.0+42` still resolve. The literal `LAlfred-` prefix and `(dmg|zip)`
# suffix do the scoping.
_FILE_PATTERN = re.compile(r"^LAlfred-[A-Za-z0-9._+-]+\.(?:dmg|zip)$")


@router.get("/appcast.xml")
async def appcast() -> RedirectResponse:
    """Sparkle appcast feed. The macOS app's `SUFeedURL` resolves here.

    Bytes flow bucket → Sparkle directly; this route only emits a 302.
    The bucket serves `appcast.xml` with `Cache-Control: max-age=300`,
    so caching lives at the right layer (shared across instances/CDNs).
    """
    target = f"{settings.release_bucket_url}/appcast.xml"
    logger.info("appcast redirect target=%s", target)
    return RedirectResponse(url=target, status_code=302)


@router.get("/download/latest")
async def download_latest() -> RedirectResponse:
    """Always-latest download link for marketing CTAs.

    Reads a small `latest.json` manifest written by CI at release time —
    the single source of truth for "what's the latest version", so we
    never have to redeploy to ship a release.
    """
    manifest: ReleaseManifest = await releases_provider.fetch_latest_manifest()
    target = f"{settings.release_bucket_url}/{manifest.dmg}"
    logger.info(
        "download redirect version=%s dmg=%s target=%s",
        manifest.version,
        manifest.dmg,
        target,
    )
    return RedirectResponse(url=target, status_code=302)


@router.get("/files/{file}")
async def release_file(file: str) -> RedirectResponse:
    """Stable per-artefact URLs used in appcast `<enclosure>` entries.

    Keeping these on our domain (vs. the raw bucket URL) lets us swap
    hosting providers later without invalidating already-cached appcasts.
    The signed `<enclosure>` inside the XML guarantees integrity, so the
    final URL doesn't have to be on our domain for security — only for
    hosting flexibility.
    """
    if not _FILE_PATTERN.match(file):
        logger.warning("release file rejected file=%s", file)
        raise HTTPException(status_code=404, detail="Not found")
    target = f"{settings.release_bucket_url}/lalfred-releases/{file}"
    logger.info("release file redirect file=%s target=%s", file, target)
    return RedirectResponse(url=target, status_code=302)
