from pydantic import BaseModel, Field


class ReleaseManifest(BaseModel):
    """Shape of `latest.json` written to the release bucket by CI at release time.

    Fields are required and non-empty so the provider can reject a malformed
    manifest at parse time with a typed error, instead of letting an empty
    string leak into a 302 to `{bucket}/` (which would be a soft footgun).
    """

    version: str = Field(..., min_length=1)
    dmg: str = Field(..., min_length=1)
