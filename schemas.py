from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator

from utils import normalize_phone_number


class RequestCodeRequest(BaseModel):
    phone_number: str = Field(..., description="WhatsApp numarası")

    @validator("phone_number")
    def validate_phone(cls, value: str) -> str:
        normalized = normalize_phone_number(value)
        if not normalized:
            raise ValueError("Geçerli bir telefon numarası giriniz.")
        return normalized


class RequestCodeResponse(BaseModel):
    phone_number: str
    verification_code: str
    expires_in_seconds: int


class VerifyCodeRequest(BaseModel):
    phone_number: str
    verification_code: str


class VerifyCodeResponse(BaseModel):
    session_token: str
    expires_in_hours: int


class ContactsUploadResponse(BaseModel):
    total_records: int
    unique_numbers: List[str]
    duplicates: List[str]
    invalid_rows: List[int]


class BaseMessageRequest(BaseModel):
    recipients: Union[str, List[str]]

    @validator("recipients")
    def ensure_list(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            return [value]
        return [str(item) for item in value]


class TextMessageRequest(BaseMessageRequest):
    message: str
    preview_url: bool = False


class MediaMessageRequest(BaseMessageRequest):
    link: str = Field(..., description="Medya için herkese açık bağlantı")
    caption: Optional[str] = None
    filename: Optional[str] = None


class MessageDispatchResult(BaseModel):
    phone_number: str
    status: str
    detail: Optional[str] = None


class MessageDispatchResponse(BaseModel):
    requested_by: str
    successful: int
    failed: int
    results: List[MessageDispatchResult]


__all__ = [
    "RequestCodeRequest",
    "RequestCodeResponse",
    "VerifyCodeRequest",
    "VerifyCodeResponse",
    "ContactsUploadResponse",
    "TextMessageRequest",
    "MediaMessageRequest",
    "MessageDispatchResponse",
    "MessageDispatchResult",
]
