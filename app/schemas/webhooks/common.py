from pydantic import BaseModel


class LemonSqueezyLinkPair(BaseModel):
    self: str | None = None
    related: str | None = None


class LemonSqueezyRelationshipLinks(BaseModel):
    links: LemonSqueezyLinkPair
