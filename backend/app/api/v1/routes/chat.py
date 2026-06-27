"""AI chat investigation routes — WebSocket streaming + REST session info."""

from __future__ import annotations

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.application.investigation.chat import ChatInvestigationUseCase
from app.container import container
from app.core import security
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


def _authorize(token: str | None) -> bool:
    """Validate the access token passed as a WS query param. Returns True if ok."""
    if not token:
        return False
    try:
        security.decode_token(token, expected_type=security.TokenType.ACCESS)
        return True
    except jwt.PyJWTError:
        return False


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket) -> None:
    """Streaming investigation chat.

    Protocol — client sends: {"type":"user_message","content":"..."}
    Server streams: agent_step | evidence | token | done | error events.
    """
    token = websocket.query_params.get("token")
    if not _authorize(token):
        await websocket.close(code=4401)  # unauthorized
        return

    await websocket.accept()
    uc = ChatInvestigationUseCase(llm=container.llm, search=container.search)

    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") != "user_message":
                continue
            question = (payload.get("content") or "").strip()
            if not question:
                continue
            async for event in uc.stream(question):
                await websocket.send_json({"type": event.type, **event.data})
    except WebSocketDisconnect:
        logger.info("chat_ws_disconnected")
    except Exception as exc:  # noqa: BLE001
        logger.warning("chat_ws_error", error=str(exc))
        try:
            await websocket.send_json({"type": "error", "message": "internal error"})
        except Exception:  # noqa: BLE001
            pass
