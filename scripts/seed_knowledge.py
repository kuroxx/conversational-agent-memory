"""Create an Enterprise Knowledge base and seed fictional bakery policies.

Usage:
    python -m scripts.seed_knowledge
    python -m scripts.seed_knowledge --knowledge-base-id know_knowledgebase_...
"""

import argparse
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from scripts.knowledge_api import KnowledgeApi

DEFAULT_CONTENT_PATH = Path(__file__).resolve().parents[1] / "assets/bakery_knowledge.md"
MAX_TEXT_CHARACTERS = 185_000


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--knowledge-base-id",
        default=os.getenv("TWILIO_KNOWLEDGE_BASE_ID"),
        help="Reuse an existing Knowledge Base instead of creating one.",
    )
    parser.add_argument("--content", type=Path, default=DEFAULT_CONTENT_PATH)
    args = parser.parse_args()

    content = args.content.read_text(encoding="utf-8")
    if len(content) > MAX_TEXT_CHARACTERS:
        raise RuntimeError(f"Knowledge content exceeds {MAX_TEXT_CHARACTERS:,} characters")

    api = KnowledgeApi.from_env()
    knowledge_base_id = args.knowledge_base_id
    if knowledge_base_id:
        print(f"Using Enterprise Knowledge Base {knowledge_base_id}")
    else:
        print("Creating Enterprise Knowledge Base...")
        knowledge_base_id = api.create_knowledge_base(
            display_name="owl-bakery-demo",
            description="Fictional bakery policies for the conversational memory demo",
        )
        print(f"  Created {knowledge_base_id}")

    print(f"Uploading {args.content.name}...")
    knowledge_id = api.add_text_source(
        knowledge_base_id,
        name="Owl Bakery Customer Policies",
        description="Delivery, pickup, allergens, order changes, and customer care",
        content=content,
    )

    print(f"  Indexed {knowledge_id}")
    print("\nAdd this value to .env:\n")
    print(f"TWILIO_KNOWLEDGE_BASE_ID={knowledge_base_id}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, httpx.HTTPError) as exc:
        raise SystemExit(f"Enterprise Knowledge setup failed: {exc}") from exc
