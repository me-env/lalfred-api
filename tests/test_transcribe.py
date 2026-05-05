from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.pricing import stt_credits

MOCK_11L_RESPONSE = {
    "text": "Hello world",
    "language_code": "en",
    "language_probability": 0.98,
    "words": [
        {"text": "Hello", "start": 0.0, "end": 0.5, "type": "word", "logprob": -0.1},
        {"text": " ", "start": 0.5, "end": 0.5, "type": "spacing", "logprob": 0.0},
        {"text": "world", "start": 0.5, "end": 1.2, "type": "word", "logprob": -0.2},
    ],
}
MOCK_DURATION_S = 1.2
EXPECTED_CREDITS = stt_credits(MOCK_DURATION_S)
EXPECTED_CREDITS_WITH_KT = stt_credits(MOCK_DURATION_S, keyterms=True)

AUDIO_FILE = ("file", ("audio.wav", b"audio-data", "audio/wav"))


def _patch_elevenlabs(response_json: dict | None = None):
    json_data = response_json or MOCK_11L_RESPONSE
    mock_response = httpx.Response(200, json=json_data)
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return patch(
        "app.providers.elevenlabs_provider.httpx.AsyncClient",
        return_value=mock_client,
    )


@pytest.mark.asyncio
async def test_transcribe_negative_balance_rejected(client, db_session, test_user, auth_token):
    test_user.credits = -1
    await db_session.commit()

    resp = await client.post(
        "/transcribe",
        headers={"Authorization": f"Bearer {auth_token}"},
        files=[AUDIO_FILE],
    )
    assert resp.status_code == 402


@pytest.mark.asyncio
async def test_transcribe_zero_balance_allowed(client, db_session, test_user, auth_token):
    test_user.credits = 0
    await db_session.commit()

    with _patch_elevenlabs():
        resp = await client.post(
            "/transcribe",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=[AUDIO_FILE],
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_transcribe_success(client, test_user, auth_token):
    with _patch_elevenlabs():
        resp = await client.post(
            "/transcribe",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=[AUDIO_FILE],
        )
        assert resp.status_code == 200
        assert resp.json()["text"] == "Hello world"


@pytest.mark.asyncio
async def test_transcribe_deducts_credits_by_duration(client, test_user, auth_token):
    initial_credits = test_user.credits

    with _patch_elevenlabs():
        await client.post(
            "/transcribe",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=[AUDIO_FILE],
        )

    balance_resp = await client.get(
        "/credits/balance", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert balance_resp.json()["credits"] == initial_credits - EXPECTED_CREDITS


@pytest.mark.asyncio
async def test_transcribe_with_keyterms_costs_more(client, test_user, auth_token):
    long_response = {
        **MOCK_11L_RESPONSE,
        "audio_duration_secs": 120.0,
    }
    base_cost = stt_credits(120.0)
    kt_cost = stt_credits(120.0, keyterms=True)
    assert kt_cost > base_cost

    initial_credits = test_user.credits

    with _patch_elevenlabs(long_response):
        resp = await client.post(
            "/transcribe",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"keyterms": ["ElevenLabs", "custom term"]},
            files=[AUDIO_FILE],
        )
    assert resp.status_code == 200

    balance_resp = await client.get(
        "/credits/balance", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert balance_resp.json()["credits"] == initial_credits - kt_cost


@pytest.mark.asyncio
async def test_transcribe_forwards_required_scribe_fields(client, auth_token):
    mock_response = httpx.Response(200, json=MOCK_11L_RESPONSE)
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.providers.elevenlabs_provider.httpx.AsyncClient",
        return_value=mock_client,
    ):
        resp = await client.post(
            "/transcribe",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=[AUDIO_FILE],
        )

    assert resp.status_code == 200
    sent_files = mock_client.post.await_args.kwargs["files"]
    sent_fields = {name: value for name, value in sent_files if name != "file"}
    assert sent_fields["model_id"][1] == "scribe_v2"
    assert sent_fields["no_verbatim"][1] == "true"
    assert sent_fields["tag_audio_events"][1] == "false"
