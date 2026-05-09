import uuid

import pytest
from app.services.notification_service import NotificationService


class FakeSmtp:
    def __init__(self, host, port, timeout=15):
        self.host = host
        self.port = port
        self.tls_started = False
        self.logged_in = False
        self.sent = []

    def starttls(self):
        self.tls_started = True

    def login(self, username, password):
        self.logged_in = (username, password)

    def sendmail(self, sender, recipients, msg_string):
        self.sent.append({"sender": sender, "recipients": recipients, "msg": msg_string})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_send_document_parsed(monkeypatch):
    import app.services.notification_service as ns
    fake = FakeSmtp("localhost", 25)
    monkeypatch.setattr(ns.smtplib, "SMTP", lambda host, port, timeout: fake)

    svc = NotificationService(smtp_host="localhost", smtp_port=25, sender="from@test.com")
    svc.send_document_parsed(
        to_email="user@test.com",
        document_title="policy.txt",
        document_version_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    )
    assert len(fake.sent) == 1
    assert fake.sent[0]["recipients"] == ["user@test.com"]


def test_send_document_failed(monkeypatch):
    import app.services.notification_service as ns
    fake = FakeSmtp("localhost", 25)
    monkeypatch.setattr(ns.smtplib, "SMTP", lambda host, port, timeout: fake)

    svc = NotificationService(sender="from@test.com")
    svc.send_document_failed(
        to_email="user@test.com",
        document_title="bad.docx",
        document_version_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        error_message="Unsupported format",
    )
    assert len(fake.sent) == 1
