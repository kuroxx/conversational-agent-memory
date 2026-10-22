"""Seed a reliable fallback memory for the live cake-order scenario."""

import argparse
import os
from datetime import UTC, datetime

from dotenv import load_dotenv

from scripts.memory_api import MemoryApi


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phone", default=os.getenv("DEMO_CUSTOMER_PHONE"))
    args = parser.parse_args()
    if not args.phone:
        parser.error("pass --phone or set DEMO_CUSTOMER_PHONE")

    api = MemoryApi.from_env()
    profile_id = api.lookup_profile(args.phone)
    if profile_id is None:
        profile = api.post(
            f"/Stores/{api.store_id}/Profiles",
            {
                "traits": {
                    "Contact": {"phone": args.phone, "firstName": "Anni"},
                }
            },
        )
        profile_id = profile["id"]

    api.post(
        f"/Stores/{api.store_id}/Profiles/{profile_id}/Observations",
        {
            "observations": [
                {
                    "content": (
                        "Customer requested changing birthday cake order 4521 "
                        "from in-store pickup to delivery. Confirm the delivery "
                        "time before updating the order."
                    ),
                    "source": "demo_seed",
                    "occurredAt": datetime.now(UTC).isoformat(),
                }
            ]
        },
    )
    print(f"Seeded demo memory for profile {profile_id}")


if __name__ == "__main__":
    main()
