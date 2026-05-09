from __future__ import annotations

import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class NotificationService:
    def __init__(
        self,
        *,
        smtp_host: str = "localhost",
        smtp_port: int = 25,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
        smtp_use_tls: bool = False,
        sender: str = "noreply@enterprise-rag.local",
    ) -> None:
        self._host = smtp_host
        self._port = smtp_port
        self._username = smtp_username
        self._password = smtp_password
        self._use_tls = smtp_use_tls
        self._sender = sender

    def send_document_parsed(
        self,
        *,
        to_email: str,
        document_title: str,
        document_version_id: uuid.UUID,
    ) -> None:
        subject = f"文档解析完成: {document_title}"
        body = (
            f"您上传的文档「{document_title}」已解析完成，可以检索使用了。\n"
            f"版本 ID: {document_version_id}"
        )
        self._send(to_email, subject, body)

    def send_document_failed(
        self,
        *,
        to_email: str,
        document_title: str,
        document_version_id: uuid.UUID,
        error_message: str,
    ) -> None:
        subject = f"文档解析失败: {document_title}"
        body = (
            f"您上传的文档「{document_title}」解析失败。\n"
            f"版本 ID: {document_version_id}\n"
            f"错误信息: {error_message}"
        )
        self._send(to_email, subject, body)

    def _send(self, to_email: str, subject: str, body: str) -> None:
        msg = MIMEMultipart()
        msg["From"] = self._sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(self._host, self._port, timeout=15) as server:
            if self._use_tls:
                server.starttls()
            if self._username and self._password:
                server.login(self._username, self._password)
            server.sendmail(self._sender, [to_email], msg.as_string())
