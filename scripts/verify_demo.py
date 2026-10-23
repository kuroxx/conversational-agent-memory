"""Fail fast if the live demo's credentials or seeded memory are missing."""

import os

from dotenv import load_dotenv

from scripts.memory_api import MemoryApi

REQUIRED_ENV = (
    "OPENAI_API_KEY",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_API_KEY",
    "TWILIO_API_SECRET",
    "TWILIO_PHONE_NUMBER",
    "TWILIO_CONVERSATION_CONFIGURATION_ID",
    "TWILIO_MEMORY_STORE_ID",
    "TWILIO_VOICE_PUBLIC_DOMAIN",
    "DEMO_CUSTOMER_PHONE",
)


def main() -> None:
    load_dotenv()
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

    api = MemoryApi.from_env()
    phone = os.environ["DEMO_CUSTOMER_PHONE"]
    profile_id = api.lookup_profile(phone)
    if profile_id is None:
        raise SystemExit(f"No Memory profile found for {phone}; run scripts.seed_profile")

    memory = api.recall(profile_id, "How will order 4521 be fulfilled?")
    recalled_text = " ".join(
        str(item.get("content", ""))
        for key in ("observations", "summaries")
        for item in memory.get(key, [])
        if isinstance(item, dict)
    )
    if "4521" not in recalled_text:
        raise SystemExit("Recall succeeded but did not return the seeded order memory")

    print(f"Demo ready: profile {profile_id} recalled order 4521")


if __name__ == "__main__":
    main()
