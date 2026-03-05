import os
import uuid
import datetime

class TwilioMock:
    """
    A Python service that mocks the Twilio SMS API.
    It simulates sending messages by logging them to the console
    in a structured format that resembles a real API response.
    """
    
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "your_sid")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "your_token")
        self.from_number = os.environ.get("TWILIO_FROM_NUMBER", "+1234567890")

    async def send_sms(self, to_number, message_body):
        # Simulate API delay or processing
        message_sid = f"SM{uuid.uuid4().hex}"
        
        print(f"\n--- [TWILIO SMS MOCK] ---")
        print(f"SID: {message_sid}")
        print(f"From: {self.from_number}")
        print(f"To: {to_number}")
        print(f"Message: {message_body}")
        print(f"Status: queued")
        print(f"-------------------------\n")
        
        return {
            "sid": message_sid,
            "status": "sent",
            "to": to_number,
            "from": self.from_number,
            "body": message_body,
            "date_created": datetime.datetime.utcnow().isoformat()
        }

# Singleton instance
twilio = TwilioMock()
