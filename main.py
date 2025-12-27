from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator

try:
    from grok_client import GrokClient
except ImportError:  # pragma: no cover - optional dependency
    GrokClient = None


class BusinessHours(BaseModel):
    timezone: str = "Europe/Istanbul"
    open_hour: int = Field(9, ge=0, le=23, description="Opening hour in 24h format")
    close_hour: int = Field(18, ge=0, le=23, description="Closing hour in 24h format")
    weekend_closed: bool = True

    @validator("close_hour")
    def validate_hours(cls, close_hour: int, values: Dict[str, int]) -> int:
        if "open_hour" in values and close_hour <= values["open_hour"]:
            raise ValueError("close_hour must be greater than open_hour")
        return close_hour


class QuickReply(BaseModel):
    title: str
    body: str


class AutomationSettings(BaseModel):
    business_name: str = "FlowChat Asistanı"
    greeting_enabled: bool = True
    greeting_message: str = (
        "Merhaba, {name}! 👋 {business} asistanına hoş geldiniz. "
        "Size nasıl yardımcı olabilirim? Sipariş durumu, randevu ya da bilgi için yazabilirsiniz."
    )
    fallback_message: str = (
        "Şu anda çevrimdışı olabiliriz ama mesajınızı aldık. "
        "Destek ekibimiz en kısa sürede sizinle iletişime geçecek."
    )
    escalation_contact: str = "Canlı Destek Temsilcisi"
    allow_after_hours_ai: bool = False
    ai_model: str = "grok-3"
    temperature: float = Field(0.4, ge=0.0, le=1.0)
    business_hours: BusinessHours = BusinessHours()
    quick_replies: List[QuickReply] = Field(
        default_factory=lambda: [
            QuickReply(title="Sipariş Takibi", body="Sipariş numaranızı paylaşır mısınız?"),
            QuickReply(title="Randevu Oluştur", body="Hangi gün ve saat için randevu almak istersiniz?"),
            QuickReply(title="Destek Talebi", body="Yaşadığınız sorunu kısaca anlatır mısınız?"),
        ]
    )
    intents: List[str] = Field(
        default_factory=lambda: [
            "sipariş_takibi",
            "randevu",
            "teknik_destek",
            "fiyatlandirma",
            "kampanya_bilgisi",
        ]
    )
    tone: str = "Profesyonel, sıcak ve hızlı yanıt veren WhatsApp müşteri temsilcisi"


class MessageRequest(BaseModel):
    sender_name: str = "Ziyaretçi"
    sender_number: str
    content: str
    conversation_id: Optional[str] = None
    new_contact: bool = False
    urgent: bool = False

    @validator("conversation_id", always=True)
    def default_conversation_id(cls, conversation_id: Optional[str], values: Dict[str, str]) -> str:
        return conversation_id or values.get("sender_number", "conversation")


class ReplyPayload(BaseModel):
    author: str
    content: str
    suggested_quick_replies: List[str] = []
    ai_model: Optional[str] = None
    type: str = "text"


class MessageResponse(BaseModel):
    conversation_id: str
    replies: List[ReplyPayload]
    routing: Dict[str, str]


app = FastAPI(
    title="WhatsApp Tarzı Akıllı Karşılama Otomasyonu",
    description="AI destekli, WhatsApp benzeri otomatik karşılama ve mesaj yönlendirme sistemi",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Your cookie values (Paste all cookies you can find in F12)
cookies = {
    "x-anonuserid": "ffdd32e1",
    "x-challenge": "TkC4D..",
    "x-signature": "fJ0...",
    "sso": "ey...",
}

client = GrokClient(cookies) if GrokClient else None

settings = AutomationSettings()
conversation_history: Dict[str, List[Dict[str, str]]] = {}


def _current_datetime(zone: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(zone))
    except Exception:
        return datetime.now()


def _is_open_for_chat(business_hours: BusinessHours) -> bool:
    now = _current_datetime(business_hours.timezone)
    if business_hours.weekend_closed and now.weekday() >= 5:
        return False
    return business_hours.open_hour <= now.hour < business_hours.close_hour


def _build_system_prompt(config: AutomationSettings, open_for_chat: bool) -> str:
    quick_replies_text = "\n".join([f"- {qr.title}: {qr.body}" for qr in config.quick_replies])
    intents_text = ", ".join(config.intents)
    business_hours_text = (
        f"Açılış: {config.business_hours.open_hour}:00, Kapanış: {config.business_hours.close_hour}:00 "
        f"(TZ: {config.business_hours.timezone}, Haftasonu kapalı: {config.business_hours.weekend_closed})"
    )
    availability = "çevrimiçi" if open_for_chat else "mesai dışı"
    return (
        f"Sen {config.business_name} adına WhatsApp kanalında çalışan akıllı bir müşteri temsilcisisin. "
        f"Ton: {config.tone}. "
        f"Şu an durum: {availability}. Mesai bilgisi: {business_hours_text}. "
        f"Destekleyebileceğin intentler: {intents_text}. "
        "Cevapların kısa, aksiyon odaklı ve WhatsApp mesajlaşma formatında olmalı. "
        "Mümkünse müşteriden net bilgiler iste ve gerekiyorsa adımlar halinde yaz. "
        "Tüm cevapların Türkçe olsun. "
        "Eğer bilgi eksikse nazikçe sor. "
        "Her mesajda en fazla iki kısa emoji kullanabilirsin."
        "\n\nHazır hızlı yanıtlar:\n"
        f"{quick_replies_text}"
    )


def _ai_reply(conversation_id: str, config: AutomationSettings, open_for_chat: bool) -> str:
    system_prompt = _build_system_prompt(config, open_for_chat)
    history = conversation_history.get(conversation_id, [])
    messages = [{"role": "system", "content": system_prompt}, *history]

    if client:
        try:
            return client.send_message(messages, temperature=config.temperature)
        except Exception:
            pass

    # Fallback lightweight heuristic
    last_user_message = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    if not open_for_chat and not config.allow_after_hours_ai:
        return (
            f"Şu an mesai dışındayız ama mesajını aldık. {config.fallback_message} "
            f"Notunu ekledim: '{last_user_message[:120]}'."
        )

    if "fiyat" in last_user_message.lower():
        return "Fiyatlarımız ürün ve pakete göre değişiyor. Hangi ürün veya hizmet için fiyat bilgisi istersiniz?"
    if "randevu" in last_user_message.lower():
        return "Randevu için tercih ettiğiniz gün ve saati yazar mısınız? Müsaitliği hemen kontrol edebilirim."
    return (
        f"Anladım, {config.business_name} olarak yardımcı oluyorum. "
        "Biraz daha detay verebilir misiniz? Sipariş numarası veya konu başlığı işimi kolaylaştırır. 😊"
    )


def _update_history(conversation_id: str, role: str, content: str) -> None:
    conversation_history.setdefault(conversation_id, []).append({"role": role, "content": content})


@app.get("/v1/models")
async def get_models():
    return jsonable_encoder(["grok-3"])


@app.get("/api/config", response_model=AutomationSettings)
async def fetch_config():
    return settings


@app.put("/api/config", response_model=AutomationSettings)
async def update_config(payload: AutomationSettings):
    global settings
    settings = payload
    return settings


@app.post("/api/messages", response_model=MessageResponse)
async def handle_message(request: MessageRequest):
    open_for_chat = _is_open_for_chat(settings.business_hours)

    _update_history(request.conversation_id, "user", request.content)

    replies: List[ReplyPayload] = []

    if settings.greeting_enabled and (request.new_contact or len(conversation_history.get(request.conversation_id, [])) <= 1):
        greeting = settings.greeting_message.format(
            name=request.sender_name or "Ziyaretçi", business=settings.business_name
        )
        replies.append(
            ReplyPayload(
                author="assistant",
                content=greeting,
                suggested_quick_replies=[qr.body for qr in settings.quick_replies],
            )
        )

    if not open_for_chat and not settings.allow_after_hours_ai:
        replies.append(
            ReplyPayload(
                author="assistant",
                content=settings.fallback_message,
                suggested_quick_replies=[],
            )
        )
        if request.urgent:
            replies.append(
                ReplyPayload(
                    author="assistant",
                    content=f"Talebinizi {settings.escalation_contact} ekibine iletiyorum. "
                    "İletişim için numaranızı doğrular mısınız?",
                )
            )
        return MessageResponse(
            conversation_id=request.conversation_id,
            replies=replies,
            routing={"status": "closed_hours", "escalation_contact": settings.escalation_contact},
        )

    ai_message = _ai_reply(request.conversation_id, settings, open_for_chat)
    _update_history(request.conversation_id, "assistant", ai_message)
    replies.append(
        ReplyPayload(
            author="assistant",
            content=ai_message,
            suggested_quick_replies=[qr.body for qr in settings.quick_replies],
            ai_model=settings.ai_model if client else "offline-fallback",
        )
    )

    return MessageResponse(
        conversation_id=request.conversation_id,
        replies=replies,
        routing={"status": "online" if open_for_chat else "after_hours", "escalation_contact": settings.escalation_contact},
    )


@app.get("/")
async def serve_home():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8046)
