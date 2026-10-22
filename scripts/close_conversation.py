"""Close a conversation so Twilio can extract observations and summaries."""

import argparse
import os

import httpx
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("conversation_id")
    args = parser.parse_args()

    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    with httpx.Client(
        base_url="https://conversations.twilio.com/v2",
        auth=(os.environ["TWILIO_API_KEY"], os.environ["TWILIO_API_SECRET"]),
        timeout=15,
    ) as client:
        response = client.patch(
            f"/Conversations/{args.conversation_id}",
            json={"status": "CLOSED"},
            headers={"X-Twilio-AccountSid": account_sid},
        )
        response.raise_for_status()
        print(response.json().get("id", args.conversation_id))


if __name__ == "__main__":
    main()
