import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TransactionType, User
from app.pricing import MAX_NEGATIVE_BALANCE, llm_credits
from app.providers import openai_provider
from app.repositories import credit_repository
from app.schemas.llm import (
    ALLOWED_MODELS,
    ChatChoice,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    TokenUsage,
)

logger = logging.getLogger(__name__)


async def chat(
    db: AsyncSession,
    user: User,
    request: ChatRequest,
) -> ChatResponse:
    if request.model not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model must be one of: {', '.join(sorted(ALLOWED_MODELS))}",
        )

    if user.credits < 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits",
        )

    raw = await openai_provider.chat(request)

    usage = raw["usage"]
    input_tokens = usage["prompt_tokens"]
    output_tokens = usage["completion_tokens"]
    cost = llm_credits(input_tokens, output_tokens, request.model)

    if user.credits - cost < MAX_NEGATIVE_BALANCE:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits",
        )

    user.credits -= cost
    await credit_repository.create(
        db,
        user_id=user.id,
        amount=-cost,
        type=TransactionType.USAGE,
        description=f"{request.model} — {input_tokens}in/{output_tokens}out",
        model=request.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    logger.info(
        "Charged %d credits to user %s (%s %din/%dout)",
        cost, user.email, request.model, input_tokens, output_tokens,
    )

    choices = raw["choices"]
    return ChatResponse(
        id=raw["id"],
        model=raw["model"],
        choices=[
            ChatChoice(
                index=c["index"],
                message=ChatMessage.model_validate(c["message"]),
                finish_reason=c.get("finish_reason"),
            )
            for c in choices
        ],
        usage=TokenUsage(
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=usage["total_tokens"],
        ),
        credits_used=cost,
    )
