import smtplib
import socket
from email.message import EmailMessage

from fastapi import HTTPException, status
from loguru import logger


class MailClient:
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        port: int,
    ):
        self.host = host
        self.user = user
        self.password = password
        self.port = port

    def send_message(self, email: EmailMessage):
        try:
            with smtplib.SMTP_SSL(self.host, self.port) as server:
                server.login(self.user, self.password)
                server.send_message(email)
        except socket.error:
            extra = {"SMTP_HOST": self.host, "SMTP_PORT": self.port}
            logger.error(
                "SMTP Exc: Error while connecting to SMTP server. Umable to send email",
                extra,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while sending email",
            )
