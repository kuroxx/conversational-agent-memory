"""Messaging tools for the bakery agent."""

import os

from agents import FunctionTool, function_tool
from twilio.base.exceptions import TwilioRestException
from twilio.http.async_http_client import AsyncTwilioHttpClient
from twilio.rest import Client

from conversation_agent.logging import log_demo

MAX_SMS_CHARACTERS = 1600


def create_send_sms_tool() -> FunctionTool:
    """Create an SMS tool configured from the environment."""

    twilio = Client(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
        http_client=AsyncTwilioHttpClient(pool_connections=False),
    )
    sms_from = os.environ["TWILIO_PHONE_NUMBER"]
    demo_customer_phone = os.environ["DEMO_CUSTOMER_PHONE"]

    @function_tool
    async def send_sms(body: str) -> dict[str, str]:
        """Send an SMS to the current demo customer after they explicitly request it."""

        message_body = body.strip()
        if not message_body:
            result = {"status": "failed", "error": "Message body cannot be empty."}
            log_demo("SMS", result)
            return result
        if len(message_body) > MAX_SMS_CHARACTERS:
            result = {
                "status": "failed",
                "error": f"Message body exceeds {MAX_SMS_CHARACTERS} characters.",
            }
            log_demo("SMS", result)
            return result

        try:
            message = await twilio.messages.create_async(
                from_=sms_from,
                to=demo_customer_phone,
                body=message_body,
            )
        except TwilioRestException as exc:
            result = {
                "status": "failed",
                "error_code": str(exc.code or "unknown"),
            }
            log_demo("SMS", result)
            return result

        result = {
            "status": "queued",
            "message_sid": message.sid,
            "to": demo_customer_phone,
        }
        log_demo("SMS", result)
        return result

    return send_sms
