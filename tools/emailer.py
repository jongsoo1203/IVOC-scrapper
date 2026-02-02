import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders


def send_email(smtp_config, subject: str, body: str, file_path: str) -> None:
    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_config.user
        msg["To"] = smtp_config.to
        msg["Subject"] = subject

        msg.attach(MIMEText(body or "", "plain"))

        with open(file_path, "rb") as file:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file.read())
            encoders.encode_base64(part)
            filename = file_path.split("/")[-1].split("\\")[-1]
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)

        with smtplib.SMTP(smtp_config.host, smtp_config.port) as server:
            server.starttls()
            server.login(smtp_config.user, smtp_config.password)
            server.send_message(msg)

    except Exception as e:
        print(f"Failed to send email: {e}")
