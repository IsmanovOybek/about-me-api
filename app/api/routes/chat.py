from fastapi import APIRouter, Depends, HTTPException, status

from app.config import get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import RagService, get_rag_service
from app.services.telegram import notify_chat_message

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    rag: RagService = Depends(get_rag_service),
) -> ChatResponse:
    settings = get_settings()
    if len(payload.message) > settings.max_message_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"message too long "
                f"(max {settings.max_message_length} characters)"
            ),
        )

    try:
        reply = rag.answer(message=payload.message, locale=payload.locale)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {exc}",
        ) from exc

    notify_chat_message(
        user_message=payload.message,
        reply=reply,
        locale=payload.locale,
        settings=settings,
    )
    return ChatResponse(reply=reply)
