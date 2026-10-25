"""Minimal client for the Conversation Memory endpoints used by demo scripts."""

import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True, slots=True)
class MemoryApi:
    """Create, look up, and recall Conversation Memory profiles."""

    store_id: str
    account_sid: str
    auth_token: str
    base_url: str = "https://memory.twilio.com/v1"

    @classmethod
    def from_env(cls) -> "MemoryApi":
        return cls(
            store_id=os.environ["TWILIO_MEMORY_STORE_ID"],
            account_sid=os.environ["TWILIO_ACCOUNT_SID"],
            auth_token=os.environ["TWILIO_AUTH_TOKEN"],
        )

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(
            base_url=self.base_url,
            auth=(self.account_sid, self.auth_token),
            timeout=15,
        ) as client:
            response = client.post(path, json=payload)
            response.raise_for_status()
            return response.json()

    def patch(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Update selected fields on an existing Memory resource."""
        with httpx.Client(
            base_url=self.base_url,
            auth=(self.account_sid, self.auth_token),
            timeout=15,
        ) as client:
            response = client.patch(path, json=payload)
            response.raise_for_status()
            return response.json()

    def lookup_profile(self, phone: str) -> str | None:
        result = self.post(
            f"/Stores/{self.store_id}/Profiles/Lookup",
            {"idType": "phone", "value": phone},
        )
        profiles = result.get("profiles", [])
        if not profiles:
            return None
        profile = profiles[0]
        return profile if isinstance(profile, str) else profile.get("id")

    def recall(
        self,
        profile_id: str,
        query: str | None = None,
        *,
        conversation_id: str | None = None,
        observations_limit: int = 5,
        summaries_limit: int = 3,
    ) -> dict[str, Any]:
        """Recall memory using conversation context, a query, or chronological recency."""
        payload: dict[str, Any] = {
            "observationsLimit": observations_limit,
            "summariesLimit": summaries_limit,
        }

        # Mode 1: Build the query from the live Orchestrator conversation context.
        if conversation_id:
            payload["conversationId"] = conversation_id

        # Mode 2: Search observations and summaries with the provided query verbatim.
        elif query:
            payload["query"] = query

        # Mode 3: With neither value set, return the most recent memories chronologically.
        return self.post(
            f"/Stores/{self.store_id}/Profiles/{profile_id}/Recall",
            payload,
        )
