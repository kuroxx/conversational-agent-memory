"""Delete Twilio demo resources by ID via the twilio-python SDK.

Usage:
    python -m scripts.cleanup memory <store-id>
    python -m scripts.cleanup orchestrator <config-id>
    python -m scripts.cleanup intelligence <config-id>
    python -m scripts.cleanup knowledge <knowledge-base-id>
    python -m scripts.cleanup profile <profile-id>

Warnings:
    Deleting a Memory Store also deletes its profiles, observations, and summaries.
    Deleting a Knowledge Base also deletes its knowledge sources.
    Profile deletion requires TWILIO_MEMORY_STORE_ID because profiles belong to a store.
"""

import argparse
import os
from collections.abc import Callable
from typing import Literal

from dotenv import load_dotenv
from twilio.rest import Client

ResourceKind = Literal["memory", "orchestrator", "intelligence", "knowledge", "profile"]
RESOURCE_KINDS: tuple[ResourceKind, ...] = (
    "memory",
    "orchestrator",
    "intelligence",
    "knowledge",
    "profile",
)

CASCADE_WARNINGS = {
    "memory": "This also deletes every profile, observation, and summary in the store.",
    "knowledge": "This also deletes every knowledge source in the knowledge base.",
}


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Set {name} in .env before running cleanup")
    return value


def _twilio_client() -> Client:
    return Client(
        _required_env("TWILIO_API_KEY"),
        _required_env("TWILIO_API_SECRET"),
        _required_env("TWILIO_ACCOUNT_SID"),
    )


def _delete_resource(client: Client, kind: ResourceKind, resource_id: str) -> bool:
    handlers: dict[ResourceKind, Callable[[], bool]] = {
        "memory": lambda: client.memory.v1.stores(resource_id).delete(),
        "orchestrator": lambda: client.conversations.v2.configurations(resource_id).delete(),
        "intelligence": lambda: client.intelligence.v3.configurations(resource_id).delete(),
        "knowledge": lambda: client.knowledge.v2.knowledge_bases(resource_id).delete(),
        "profile": lambda: client.memory.v1.profiles(
            _required_env("TWILIO_MEMORY_STORE_ID"),
            resource_id,
        ).delete(),
    }
    return handlers[kind]()


def _confirm(kind: ResourceKind, resource_id: str) -> bool:
    print(f"Delete {kind} resource {resource_id}?")
    if warning := CASCADE_WARNINGS.get(kind):
        print(f"WARNING: {warning}")
    return input("Type yes to confirm: ").strip().lower() == "yes"


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=RESOURCE_KINDS)
    parser.add_argument("resource_id")
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    kind: ResourceKind = args.kind
    resource_id: str = args.resource_id
    if not args.yes and not _confirm(kind, resource_id):
        print("Deletion cancelled.")
        return

    print(f"Deleting {kind} {resource_id}...")
    if not _delete_resource(_twilio_client(), kind, resource_id):
        raise RuntimeError(f"Twilio did not confirm deletion of {kind} {resource_id}")
    print("Deleted.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"Cleanup failed: {exc}") from exc
