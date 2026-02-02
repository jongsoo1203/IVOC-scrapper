from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


@dataclass(frozen=True)
class Emailer:
    smtp_host: str
    smtp_port: int
    user: str
    password: str

    def send_with_attachment(
        self,
        recipient: str,
        subject: str,
        body: str,
        attachment_path: Path,
    ) -> None:
        msg = MIMEMultipart()
        msg["From"] = self.user
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with attachment_path.open("rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{attachment_path.name}"')
            msg.attach(part)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.user, self.password)
            server.send_message(msg)
