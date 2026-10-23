"""Create the Twilio resources required by the SMS + Voice memory demo.

The Memory Store and Conversation Configuration are asynchronous operations.
This script creates them in the required order, polls each operation until it
completes, and prints the values to add to ``.env``.

Usage:
    python -m scripts.setup
"""

import base64
import json
import os
import sys
import time
import urllib.request
from typing import Any

from dotenv import load_dotenv

POLL_ATTEMPTS = 60
POLL_INTERVAL_SECONDS = 3


def _load_sdk() -> tuple[Any, Any, Any]:
    """Load the generated Twilio resources with an actionable version error."""

    try:
        from twilio.rest import Client
        from twilio.rest.conversations.v2 import ConfigurationList
        from twilio.rest.memory.v1 import StoreList
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Your installed twilio package does not include Conversation Memory and "
            "Conversation Orchestrator. Upgrade the Twilio Python SDK, then retry: "
            "pip install --upgrade twilio"
        ) from exc
    return Client, StoreList, ConfigurationList


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Set {name} in .env before running setup")
    return value


def _basic_auth(api_key: str, api_secret: str) -> str:
    encoded = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    return f"Basic {encoded}"


def _status_callback_url() -> str:
    override = os.getenv("TWILIO_STATUS_CALLBACK_URL")
    if override:
        return override

    domain = _required_env("TWILIO_VOICE_PUBLIC_DOMAIN").strip().rstrip("/")
    for scheme in ("https://", "http://", "wss://", "ws://"):
        if domain.lower().startswith(scheme):
            domain = domain[len(scheme) :]
            break
    return f"https://{domain}/webhook"


def wait_for(
    status_url: str,
    label: str,
    authorization: str,
    *,
    attempts: int = POLL_ATTEMPTS,
    interval_seconds: float = POLL_INTERVAL_SECONDS,
) -> dict[str, Any]:
    """Poll an asynchronous Twilio operation and return its result."""

    for _ in range(attempts):
        request = urllib.request.Request(
            status_url,
            headers={"Authorization": authorization, "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            operation = json.loads(response.read())

        status = operation.get("status", "").upper()
        if status == "COMPLETED":
            return operation.get("resource") or operation.get("result") or operation
        if status == "FAILED":
            raise RuntimeError(f"{label} failed: {operation}")
        time.sleep(interval_seconds)

    raise RuntimeError(f"{label} timed out after {attempts} status checks")


def _resource_id(result: dict[str, Any], label: str) -> str:
    """Read IDs from the result shapes returned by Twilio async operations."""

    related = result.get("related") or {}
    resource_id = (
        result.get("id") or result.get("configurationId") or related.get("configurationId")
    )
    if not resource_id:
        raise RuntimeError(f"{label} completed but returned no resource ID: {result}")
    return str(resource_id)


def create_resources() -> tuple[str, str]:
    Client, StoreList, ConfigurationList = _load_sdk()

    api_key = _required_env("TWILIO_API_KEY")
    api_secret = _required_env("TWILIO_API_SECRET")
    account_sid = _required_env("TWILIO_ACCOUNT_SID")
    twilio_number = _required_env("TWILIO_PHONE_NUMBER")
    callback_url = _status_callback_url()

    client = Client(api_key, api_secret, account_sid)
    authorization = _basic_auth(api_key, api_secret)

    print("Creating Conversation Memory Store...")
    store_operation = client.memory.v1.stores.create(
        service_request=StoreList.ServiceRequest(
            {
                "displayName": "conversation-agent-demo-memory",
                "description": "Customer memory for the SMS and Voice agent demo",
            }
        )
    )
    store_result = wait_for(
        store_operation.status_url,
        "Memory Store",
        authorization,
    )
    store_id = _resource_id(store_result, "Memory Store")
    print(f"  Created {store_id}\n")

    ChannelSetting = ConfigurationList.CreateConfigurationRequestChannelSettingsValue
    CaptureRule = ConfigurationList.CreateConfigurationRequestChannelSettingsValueCaptureRules
    Timeouts = ConfigurationList.CreateConfigurationRequestChannelSettingsValueStatusTimeouts
    StatusCallback = ConfigurationList.CreateConfigurationRequestStatusCallbacks

    sms_capture_rules = [
        CaptureRule({"from": "*", "to": twilio_number}),
        CaptureRule({"from": twilio_number, "to": "*"}),
    ]
    sms_timeouts = Timeouts({"inactive": 5, "closed": 15})

    print("Creating Conversation Orchestrator Configuration...")
    configuration_operation = client.conversations.v2.configurations.create(
        create_configuration_request=ConfigurationList.CreateConfigurationRequest(
            {
                "displayName": "conversation-agent-demo",
                "description": "Unifies SMS and ConversationRelay Voice customer context",
                "conversationGroupingType": "GROUP_BY_PROFILE",
                "memoryStoreId": store_id,
                "memoryExtractionEnabled": True,
                "channelSettings": {
                    "SMS": ChannelSetting(
                        {
                            "captureRules": sms_capture_rules,
                            "statusTimeouts": sms_timeouts,
                        }
                    ),
                    # Agent Connect actively ingests ConversationRelay Voice.
                    # Omitting Voice capture rules avoids duplicate transcription billing.
                    "VOICE": ChannelSetting({"statusTimeouts": None}),
                },
                "statusCallbacks": [StatusCallback({"url": callback_url, "method": "POST"})],
            }
        )
    )
    configuration_result = wait_for(
        configuration_operation.status_url,
        "Conversation Configuration",
        authorization,
    )
    configuration_id = _resource_id(
        configuration_result,
        "Conversation Configuration",
    )
    print(f"  Created {configuration_id}\n")
    return store_id, configuration_id


def main() -> None:
    load_dotenv()
    store_id, configuration_id = create_resources()

    print("Add these values to .env:\n")
    print(f"TWILIO_MEMORY_STORE_ID={store_id}")
    print(f"TWILIO_CONVERSATION_CONFIGURATION_ID={configuration_id}")
    print("\nNext: python -m scripts.seed_profile && python -m scripts.seed_knowledge")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
