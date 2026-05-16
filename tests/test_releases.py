import pytest
from fastapi import HTTPException

from app.config import settings
from app.providers import releases_provider
from app.schemas.releases import ReleaseManifest


@pytest.mark.asyncio
async def test_appcast_redirects_to_bucket(client):
    resp = await client.get("/releases/appcast.xml")
    assert resp.status_code == 302
    assert resp.headers["location"] == f"{settings.release_bucket_url}/appcast.xml"


@pytest.mark.asyncio
async def test_download_latest_redirects_to_dmg(client, monkeypatch):
    async def fake_fetch():
        return ReleaseManifest(version="1.2.0", dmg="lalfred-releases/LAlfred-1.2.0.dmg")

    monkeypatch.setattr(releases_provider, "fetch_latest_manifest", fake_fetch)
    resp = await client.get("/releases/download/latest")
    assert resp.status_code == 302
    assert resp.headers["location"] == (
        f"{settings.release_bucket_url}/lalfred-releases/LAlfred-1.2.0.dmg"
    )


@pytest.mark.asyncio
async def test_download_latest_502_when_manifest_unreachable(client, monkeypatch):
    async def fake_fetch():
        raise HTTPException(status_code=502, detail="Release manifest unavailable")

    monkeypatch.setattr(releases_provider, "fetch_latest_manifest", fake_fetch)
    resp = await client.get("/releases/download/latest")
    assert resp.status_code == 502


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        b'{"version": "1.2.0"}',  # missing dmg
        b'{"dmg": "x"}',  # missing version
        b'{"version": "", "dmg": "x"}',  # empty version
        b'{"version": "1.2.0", "dmg": ""}',  # empty dmg
        b"not json",
    ],
)
async def test_download_latest_502_when_manifest_malformed(client, monkeypatch, body):
    """Malformed upstream manifests should surface as 502, not 500."""
    import httpx

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, *args, **kwargs):
            return httpx.Response(200, content=body)

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    resp = await client.get("/releases/download/latest")
    assert resp.status_code == 502


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filename",
    [
        "LAlfred-1.2.0.dmg",
        "LAlfred-1.2.0.zip",
        "LAlfred-1.2.0-beta.3.dmg",
        "LAlfred-1.2.0+42.dmg",
        "LAlfred-0.1.0-rc1.zip",
    ],
)
async def test_release_file_accepts_valid_names(client, filename):
    resp = await client.get(f"/releases/files/{filename}")
    assert resp.status_code == 302
    assert resp.headers["location"] == (
        f"{settings.release_bucket_url}/lalfred-releases/{filename}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filename",
    [
        "evil.exe",
        "LAlfred-1.2.0.exe",
        "LAlfred-.dmg",
        "other-1.2.0.dmg",
        "LAlfred-1.2.0",
        "LAlfred-1.2.0.dmg.exe",
        "LAlfred 1.2.0.dmg",
    ],
)
async def test_release_file_rejects_invalid_names(client, filename):
    resp = await client.get(f"/releases/files/{filename}")
    assert resp.status_code == 404
