from __future__ import annotations

from typing import Awaitable, Callable, List

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from auth import AuthManager
from contacts import ContactsProcessor
from schemas import (
    ContactsUploadResponse,
    MediaMessageRequest,
    MessageDispatchResponse,
    MessageDispatchResult,
    RequestCodeRequest,
    RequestCodeResponse,
    TextMessageRequest,
    VerifyCodeRequest,
    VerifyCodeResponse,
)
from utils import deduplicate_numbers, normalize_phone_number
from whatsapp_client import WhatsAppClient

app = FastAPI(
    title="WhatsApp Otomasyon API",
    description="WhatsApp kod ile giriş, toplu mesajlaşma ve CSV kişi yönetimi için servis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_manager = AuthManager()
contacts_processor = ContactsProcessor()
whatsapp_client = WhatsAppClient()


def require_session(x_session_token: str = Header(..., alias="X-Session-Token")) -> str:
    try:
        return auth_manager.validate_session(x_session_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@app.post("/auth/request-code", response_model=RequestCodeResponse)
async def request_code(payload: RequestCodeRequest) -> RequestCodeResponse:
    try:
        code = auth_manager.request_code(payload.phone_number)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return RequestCodeResponse(
        phone_number=payload.phone_number,
        verification_code=code,
        expires_in_seconds=300,
    )


@app.post("/auth/verify-code", response_model=VerifyCodeResponse)
async def verify_code(payload: VerifyCodeRequest) -> VerifyCodeResponse:
    try:
        token = auth_manager.verify_code(payload.phone_number, payload.verification_code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return VerifyCodeResponse(session_token=token, expires_in_hours=12)


@app.post("/contacts/upload", response_model=ContactsUploadResponse)
async def upload_contacts(
    file: UploadFile = File(...),
    _: str = Depends(require_session),
) -> ContactsUploadResponse:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lütfen CSV formatında bir dosya yükleyin.")
    data = await file.read()
    try:
        result = contacts_processor.process_csv_bytes(data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ContactsUploadResponse(**result.__dict__)


async def _dispatch_messages(
    session_owner: str,
    recipients: List[str],
    sender: Callable[[str], Awaitable[dict]],
) -> MessageDispatchResponse:
    normalized_numbers = [normalize_phone_number(number) for number in recipients]
    unique_numbers, duplicates = deduplicate_numbers(normalized_numbers)

    results: List[MessageDispatchResult] = []
    successful = 0
    failed = 0

    for duplicate in duplicates:
        results.append(
            MessageDispatchResult(
                phone_number=duplicate,
                status="skipped",
                detail="Yinelenen numara olduğu için atlandı.",
            )
        )

    for phone in unique_numbers:
        if not phone:
            results.append(
                MessageDispatchResult(
                    phone_number=phone,
                    status="failed",
                    detail="Telefon numarası doğrulanamadı.",
                )
            )
            failed += 1
            continue
        try:
            result = await sender(phone)
        except Exception as exc:  # pylint: disable=broad-except
            results.append(
                MessageDispatchResult(
                    phone_number=phone,
                    status="failed",
                    detail=str(exc),
                )
            )
            failed += 1
        else:
            detail = None
            if isinstance(result, dict):
                message_ids = ", ".join(msg.get("id", "") for msg in result.get("messages", []) if msg.get("id"))
                detail = f"message_id={message_ids}" if message_ids else None
            results.append(
                MessageDispatchResult(
                    phone_number=phone,
                    status="sent",
                    detail=detail,
                )
            )
            successful += 1

    return MessageDispatchResponse(
        requested_by=session_owner,
        successful=successful,
        failed=failed,
        results=results,
    )


@app.post("/messages/send-text", response_model=MessageDispatchResponse)
async def send_text_message(
    payload: TextMessageRequest,
    session_owner: str = Depends(require_session),
) -> MessageDispatchResponse:
    async def _sender(phone: str) -> dict:
        return await whatsapp_client.send_text_message(phone, payload.message, payload.preview_url)

    return await _dispatch_messages(session_owner, payload.recipients, _sender)


@app.post("/messages/send-image", response_model=MessageDispatchResponse)
async def send_image_message(
    payload: MediaMessageRequest,
    session_owner: str = Depends(require_session),
) -> MessageDispatchResponse:
    async def _sender(phone: str) -> dict:
        return await whatsapp_client.send_image_message(phone, payload.link, payload.caption)

    return await _dispatch_messages(session_owner, payload.recipients, _sender)


@app.post("/messages/send-document", response_model=MessageDispatchResponse)
async def send_document_message(
    payload: MediaMessageRequest,
    session_owner: str = Depends(require_session),
) -> MessageDispatchResponse:
    async def _sender(phone: str) -> dict:
        return await whatsapp_client.send_document_message(
            phone,
            payload.link,
            filename=payload.filename,
            caption=payload.caption,
        )

    return await _dispatch_messages(session_owner, payload.recipients, _sender)


@app.on_event("startup")
async def startup_event() -> None:
    auth_manager.cleanup_expired_sessions()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8046)
