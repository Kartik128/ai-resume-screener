import logging
from typing import Optional
from app.models.user import User

logger = logging.getLogger(__name__)

class ProviderMailClient:
    """
    A unified Interface wrapper that handles sending emails dynamically depending 
    on the user's active configuration (Google Gmail API, Microsoft Graph API, or standard SMTP).
    """
    def __init__(self, user: User):
        self.user = user
        self.provider = user.mail_provider or "smtp"

    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        if self.provider == "google":
            logger.info(f"📧 Sending email via Google API (User {self.user.email}) -> {to_email}")
            # Real Google Gmail API connection mock
            return True
        elif self.provider == "microsoft":
            logger.info(f"📧 Sending email via Microsoft Graph API (User {self.user.email}) -> {to_email}")
            # Real Microsoft Exchange Graph API connection mock
            return True
        else:
            logger.info(f"📧 Sending email via Generic SMTP fallback -> {to_email}")
            # SMTP protocol fallback connection mock
            return True

    async def create_calendar_event(self, attendee_email: str, title: str, start_time: str, duration_mins: int = 30) -> Optional[str]:
        if self.provider == "google":
            logger.info(f"📅 Booking Google Calendar slot for {attendee_email}")
            return f"https://meet.google.com/mock-{self.user.id}"
        elif self.provider == "microsoft":
            logger.info(f"📅 Booking Microsoft Teams Outlook slot for {attendee_email}")
            return f"https://teams.microsoft.com/l/meetup-join/mock-{self.user.id}"
        else:
            logger.info(f"📅 Booking Generic calendar slot for {attendee_email}")
            return "https://calendar.mock-system.org/event/123"
