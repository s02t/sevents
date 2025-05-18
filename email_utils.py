from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List, Dict, Any
import qrcode
import io
import base64
from config import email_config
from pydantic import EmailStr

# Configure mail settings
conf = ConnectionConfig(
    MAIL_USERNAME=email_config.MAIL_USERNAME,
    MAIL_PASSWORD=email_config.MAIL_PASSWORD,
    MAIL_FROM=email_config.MAIL_FROM,
    MAIL_PORT=email_config.MAIL_PORT,
    MAIL_SERVER=email_config.MAIL_SERVER,
    MAIL_FROM_NAME=email_config.MAIL_FROM_NAME,
    MAIL_STARTTLS=email_config.MAIL_STARTTLS,
    MAIL_SSL_TLS=email_config.MAIL_SSL_TLS,
    USE_CREDENTIALS=email_config.USE_CREDENTIALS,
    VALIDATE_CERTS=email_config.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path("templates/email")
)

# Class to handle email operations
class EmailManager:
    @staticmethod
    async def send_registration_email(
        email_to: str,
        subject: str,
        body: Dict[str, Any]
    ):
        """Send registration confirmation email with QR code"""
        try:
            # Generate QR code
            qr_data = body.get("qr_uuid", "")
            qr_img = qrcode.make(qr_data)
            
            # Convert QR code to base64 for embedding in email
            buffered = io.BytesIO()
            qr_img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Add QR code to body data
            body["qr_base64"] = qr_base64
            
            # Create message
            message = MessageSchema(
                subject=subject,
                recipients=[email_to],
                template_body=body,
                subtype=MessageType.html,
            )
            
            # Send email
            fm = FastMail(conf)
            await fm.send_message(message, template_name="registration_confirmation.html")
            
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
            
    @staticmethod
    async def send_event_update(
        email_to: List[str],
        subject: str,
        body: Dict[str, Any]
    ):
        """Send event updates to multiple recipients"""
        try:
            message = MessageSchema(
                subject=subject,
                recipients=email_to,
                template_body=body,
                subtype=MessageType.html,
            )
            
            fm = FastMail(conf)
            await fm.send_message(message, template_name="event_update.html")
            
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False 