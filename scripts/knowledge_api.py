"""Minimal client for the Enterprise Knowledge endpoints used by demo scripts."""

import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx

POLL_ATTEMPTS = 60
POLL_INTERVAL_SECONDS = 3


@dataclass(frozen=True, slots=True)
class KnowledgeApi:
    """Create and populate Enterprise Knowledge bases."""

    account_sid: str
    auth_token: str
    base_url: str = "https://knowledge.twilio.com/v2"

    @classmethod
    def from_env(cls) -> "KnowledgeApi":
        return cls(
            account_sid=os.environ["TWILIO_ACCOUNT_SID"],
            auth_token=os.environ["TWILIO_AUTH_TOKEN"],
        )

    def create_knowledge_base(self, display_name: str, description: str) -> str:
        with self._client() as client:
            response = client.post(
                "/ControlPlane/KnowledgeBases",
                json={"displayName": display_name, "description": description},
            )
            response.raise_for_status()
            response_data = response.json()
            operation_url = response_data.get("statusUrl") or response.headers.get("Location")
            if not operation_url:
                raise RuntimeError(
                    f"Knowledge Base creation returned no status URL: {response_data}"
                )

            result = self._wait_for(
                client,
                urljoin(self.base_url, operation_url),
                label="Knowledge Base",
            )

        resource = result.get("resource") or result.get("result") or result
        if not isinstance(resource, dict):
            raise RuntimeError(f"Knowledge Base creation returned an invalid result: {result}")
        knowledge_base_id = resource.get("id")
        if not knowledge_base_id:
            raise RuntimeError(f"Knowledge Base creation returned no ID: {result}")
        return str(knowledge_base_id)

    def add_text_source(
        self,
        knowledge_base_id: str,
        *,
        name: str,
        description: str,
        content: str,
    ) -> str:
        with self._client() as client:
            response = client.post(
                f"/KnowledgeBases/{knowledge_base_id}/Knowledge",
                json={
                    "name": name,
                    "description": description,
                    "source": {"type": "Text", "content": content},
                },
            )
            response.raise_for_status()
            knowledge_id = response.json().get("id")
            if not knowledge_id:
                raise RuntimeError(f"Knowledge source creation returned no ID: {response.text}")

            self._wait_for(
                client,
                f"/KnowledgeBases/{knowledge_base_id}/Knowledge/{knowledge_id}",
                label="Knowledge source",
            )
            return str(knowledge_id)

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            auth=(self.account_sid, self.auth_token),
            timeout=30,
        )

    def _wait_for(
        self,
        client: httpx.Client,
        url: str,
        *,
        label: str,
    ) -> dict[str, Any]:
        for _ in range(POLL_ATTEMPTS):
            response = client.get(url)
            response.raise_for_status()
            result = response.json()
            status = str(result.get("status", "")).upper()
            if status == "COMPLETED":
                return result
            if status == "FAILED":
                raise RuntimeError(f"{label} processing failed: {result}")
            time.sleep(POLL_INTERVAL_SECONDS)

        raise RuntimeError(f"{label} timed out after {POLL_ATTEMPTS} status checks")
