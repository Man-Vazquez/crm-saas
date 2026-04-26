from __future__ import annotations
import asyncio
import email as email_lib
import imaplib
import logging
import re
import smtplib
from email.header import decode_header, make_header
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

    def _decode_subject(self, raw: str) -> str:
        """Decode an RFC 2047 encoded subject (=?UTF-8?Q?...?= / =?ISO-8859-1?B?...?=)."""
        try:
            return str(make_header(decode_header(raw)))
        except Exception:
            return raw

    def _strip_html(self, html: str) -> str:
        """Minimal HTML-to-text fallback when no text/plain part exists."""
        text = re.sub(r'<[^>]+>', '', html)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        return re.sub(r'\n{3,}', '\n\n', text).strip()

    def _parse_email_object(self, parsed_email) -> InboundMessage | None:
        try:
            from_raw    = parsed_email.get("From", "")
            to_raw      = parsed_email.get("To", "")
            subject_raw = parsed_email.get("Subject", "")
            subject     = self._decode_subject(subject_raw)   # Bug 1 fix: RFC 2047 decoding
            msg_id      = parsed_email.get("Message-ID", from_raw)

            # Bug 2 fix: explicit two-pass extraction — prefer text/plain, fall back to
            # text/html with tag stripping.  The previous single-pass loop broke on emails
            # where text/html appeared before text/plain in the MIME tree.
            plain_body = ""
            html_body  = ""
            if parsed_email.is_multipart():
                for part in parsed_email.walk():
                    ct = part.get_content_type()
                    if ct == "text/plain" and not plain_body:
                        plain_body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    elif ct == "text/html" and not html_body:
                        html_body = part.get_payload(decode=True).decode("utf-8", errors="replace")
            else:
                raw = parsed_email.get_payload(decode=True).decode("utf-8", errors="replace")
                ct  = parsed_email.get_content_type()
                if ct == "text/html":
                    html_body = raw
                else:
                    plain_body = raw

            # body  = texto plano → usado para search_vector (trigger de PostgreSQL)
            # body_html = HTML original → renderizado en el frontend con DOMPurify
            if html_body and plain_body:
                body = plain_body
            elif html_body:
                body = self._strip_html(html_body)
            else:
                body = plain_body

            body_html = html_body if html_body else None

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
                    "body_html": body_html,
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