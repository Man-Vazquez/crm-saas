from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class InboundMessage:
    """
    Mensaje normalizado que llega desde cualquier canal.
    El adapter de cada canal convierte su formato nativo a este.
    """
    external_id: str        # ID del mensaje en el canal (msg_id de WhatsApp, email Message-ID)
    from_address: str       # email del remitente o número de teléfono
    to_address: str         # email destino o número del negocio
    subject: str | None     # solo relevante para email
    body: str               # cuerpo del mensaje en texto plano
    channel_type: str       # "email" | "whatsapp"
    raw_payload: dict       # payload original sin modificar — para debugging


@dataclass
class OutboundMessage:
    """
    Mensaje que el sistema quiere enviar por un canal.
    El adapter de cada canal lo convierte a su formato nativo.
    """
    to_address: str         # email destino o número de teléfono
    body: str               # cuerpo del mensaje
    subject: str | None     # solo para email
    reply_to_external_id: str | None  # para threading en email


class BaseChannel(ABC):
    """
    Interfaz que todo canal debe implementar.
    
    Regla: el resto del sistema solo habla con BaseChannel,
    nunca con EmailChannel o WhatsAppChannel directamente.
    """

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """Identificador del canal: 'email', 'whatsapp', etc."""
        ...

    @abstractmethod
    async def send(self, message: OutboundMessage) -> bool:
        """
        Envía un mensaje saliente por este canal.
        Devuelve True si se envió correctamente, False si falló.
        """
        ...

    @abstractmethod
    def parse_inbound(self, raw_payload: dict) -> InboundMessage | None:
        """
        Convierte el payload crudo del webhook al formato InboundMessage.
        Devuelve None si el payload no es un mensaje válido (ej: evento de estado).
        """
        ...

    @abstractmethod
    def verify_webhook(self, params: dict) -> bool:
        """
        Verifica que el webhook viene del proveedor legítimo.
        Email: siempre True (verificación por IP/token en header).
        WhatsApp: valida el challenge de Meta.
        """
        ...