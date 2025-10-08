from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


DEFAULT_BASE_URL = "https://graph.facebook.com/v18.0"


class WhatsAppClient:
    """Lightweight wrapper for the WhatsApp Cloud API."""

    def __init__(
        self,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        request_timeout: float = 15.0,
    ) -> None:
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.base_url = base_url.rstrip("/")
        self.request_timeout = request_timeout

    def _check_configuration(self) -> None:
        if not self.phone_number_id or not self.access_token:
            raise RuntimeError(
                "WhatsApp API bilgileri eksik. Lütfen WHATSAPP_PHONE_NUMBER_ID ve WHATSAPP_ACCESS_TOKEN değerlerini ayarlayın."
            )

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._check_configuration()
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.request_timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise RuntimeError(f"WhatsApp API hatası: {response.status_code} - {response.text}")
        return response.json()

    async def send_text_message(self, phone_number: str, message: str, preview_url: bool = False) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message, "preview_url": preview_url},
        }
        return await self._post(payload)

    async def send_image_message(self, phone_number: str, image_link: str, caption: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "image",
            "image": {"link": image_link},
        }
        if caption:
            payload["image"]["caption"] = caption
        return await self._post(payload)

    async def send_document_message(
        self,
        phone_number: str,
        document_link: str,
        filename: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "document",
            "document": {"link": document_link},
        }
        if filename:
            payload["document"]["filename"] = filename
        if caption:
            payload["document"]["caption"] = caption
        return await self._post(payload)


__all__ = ["WhatsAppClient"]
