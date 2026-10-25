"""Recall context for the demo customer's Memory profile.

Usage:
    python -m scripts.recall_memory
    python -m scripts.recall_memory --conversation-id <conversation-id>
    python -m scripts.recall_memory "shipping preference" \
        --observations-limit 5 --summaries-limit 2
"""

import argparse
import json
import os

from dotenv import load_dotenv

from scripts.memory_api import MemoryApi


def main() -> None:
    """Look up the configured demo profile and print its recalled context."""
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", help="Optional custom query")
    parser.add_argument(
        "--conversation-id",
        help="Use a live Orchestrator conversation to build the recall query",
    )
    parser.add_argument("--observations-limit", type=int, default=3)
    parser.add_argument("--summaries-limit", type=int, default=3)
    args = parser.parse_args()

    api = MemoryApi.from_env()
    phone = os.environ["DEMO_CUSTOMER_PHONE"]
    profile_id = api.lookup_profile(phone)
    if profile_id is None:
        raise SystemExit(f"No Memory profile found for {phone}; run scripts.seed_profile")

    result = api.recall(
        profile_id,
        query=args.query,
        conversation_id=args.conversation_id,
        observations_limit=args.observations_limit,
        summaries_limit=args.summaries_limit,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
