"""Minimal client for the Conversation Memory endpoints used by demo scripts."""

import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True, slots=True)
class MemoryApi:
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

    def recall(self, profile_id: str, query: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"observationsLimit": 5, "summariesLimit": 3}
        if query:
            payload["query"] = query
        return self.post(
            f"/Stores/{self.store_id}/Profiles/{profile_id}/Recall",
            payload,
        )
