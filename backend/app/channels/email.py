from __future__ import annotations
import asyncio
import email as email_lib
import imaplib
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.channels.base import BaseChannel, InboundMessage, OutboundMessage
from app.core.encryption import decrypt_config

logger = logging.getLogger(__name__)

class EmailChannel(BaseChannel):

    def __init__(self, config: dict):
        self.config = decrypt_config(config)

    @property
    def channel_type(self) -> str:
        return "email"

    async def send(self, message: OutboundMessage) -> bool:
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_sync, message
            )
            logger.info(f"Email enviado a {message.to_address}")
            return True
        except Exception as e:
            logger.error(f"Error enviando email a {message.to_address}: {e}")
            return False

    def _send_sync(self, message: OutboundMessage) -> None:
        msg = MIMEMultipart("alternative")
        from_name  = self.config.get("from_name", "Soporte")
        from_email = self.config["smtp_user"]

        msg["Subject"] = message.subject or "Re: Tu solicitud"
        msg["From"]    = f"{from_name} <{from_email}>"
        msg["To"]      = message.to_address

        if message.reply_to_external_id:
            msg["In-Reply-To"] = message.reply_to_external_id
            msg["References"]  = message.reply_to_external_id

        msg.attach(MIMEText(message.body, "plain", "utf-8"))

        with smtplib.SMTP(self.config["smtp_host"], int(self.config["smtp_port"])) as server:
            server.ehlo()
            server.starttls()
            server.login(self.config["smtp_user"], self.config["smtp_password"])
            server.sendmail(from_email, message.to_address, msg.as_string())

    def fetch_unread_emails(self) -> list[InboundMessage]:
        messages = []
        try:
            imap = imaplib.IMAP4_SSL(
                self.config["imap_host"],
                int(self.config.get("imap_port", 993))
            )
            imap.login(self.config["smtp_user"], self.config["smtp_password"])
            imap.select("INBOX")

            _, message_ids = imap.search(None, "UNSEEN")

            for msg_id in message_ids[0].split():
                try:
                    _, msg_data = imap.fetch(msg_id, "(RFC822)")
                    raw_email  = msg_data[0][1]
                    parsed     = email_lib.message_from_bytes(raw_email)
                    inbound    = self._parse_email_object(parsed)

                    if inbound:
                        messages.append(inbound)
                        imap.store(msg_id, "+FLAGS", "\\Seen")
                        # DEUDA TÉCNICA: Etiquetado en Gmail requiere Gmail API con OAuth2,
                        # no IMAP estándar. Ver: messages.modify con addLabelIds.
                        # Por ahora usamos SEEN como mecanismo anti-duplicados.

                except Exception as e:
                    logger.error(f"Error procesando email {msg_id}: {e}")
                    continue

            imap.logout()
            logger.info(f"IMAP: {len(messages)} emails nuevos encontrados")

        except Exception as e:
            logger.error(f"Error conectando a IMAP: {e}")

        return messages

    def _parse_email_object(self, parsed_email) -> InboundMessage | None:
        try:
            from_raw = parsed_email.get("From", "")
            to_raw   = parsed_email.get("To", "")
            subject  = parsed_email.get("Subject", "")
            msg_id   = parsed_email.get("Message-ID", from_raw)

            body = ""
            if parsed_email.is_multipart():
                for part in parsed_email.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        break
            else:
                body = parsed_email.get_payload(decode=True).decode("utf-8", errors="replace")

            from_email = self._extract_email(from_raw)
            to_email   = self._extract_email(to_raw)

            if not from_email:
                return None

            in_reply_to = parsed_email.get("In-Reply-To", "").strip() or None

            return InboundMessage(
                external_id=msg_id.strip(),
                from_address=from_email,
                to_address=to_email,
                subject=subject,
                body=body.strip(),
                channel_type="email",
                raw_payload={
                    "from": from_raw,
                    "to": to_raw,
                    "subject": subject,
                    "message_id": msg_id,
                    "in_reply_to": in_reply_to,
                    "body": body.strip(),
                },
            )
        except Exception as e:
            logger.error(f"Error parseando email: {e}")
            return None

    def parse_inbound(self, raw_payload: dict) -> InboundMessage | None:
        return None

    def verify_webhook(self, params: dict) -> bool:
        return True

    def _extract_email(self, raw: str) -> str:
        if "<" in raw and ">" in raw:
            return raw.split("<")[1].split(">")[0].strip()
        return raw.strip()