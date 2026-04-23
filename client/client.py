import uuid
from typing import Optional

import httpx


class A2AClient:
    """Minimal A2A-compliant client."""

    def __init__(self, agent_url: str):
        self.agent_url = agent_url.rstrip("/")
        self._card = None
        self._http = httpx.Client(timeout=30)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        self._http.close()

    def fetch_agent_card(self) -> dict:
        """Fetch and cache the Agent Card."""
        if self._card is None:
            url = f"{self.agent_url}/.well-known/agent.json"
            print(f"[CLIENT] GET {url}")
            resp = self._http.get(url)
            print(f"[CLIENT] Response {resp.status_code}: {resp.text[:200]}")
            resp.raise_for_status()
            self._card = resp.json()
        return self._card

    def get_skills(self) -> list:
        """Return the skills list from the cached Agent Card."""
        card = self.fetch_agent_card()
        return card.get("skills", [])

    def _build_task(
        self,
        text: str,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> dict:
        """Build a conformant A2A task payload."""
        return {
            "id": task_id or str(uuid.uuid4()),
            "sessionId": session_id,
            "message": {
                "role": "user",
                "parts": [
                    {"type": "text", "text": text}
                ]
            }
        }

    def send_task(self, text: str, **kwargs) -> dict:
        """Send a task and return the parsed response."""
        self.fetch_agent_card()

        payload = self._build_task(text, **kwargs)
        url = f"{self.agent_url}/tasks/send"

        print(f"[CLIENT] POST {url}")
        print(f"[CLIENT] Payload: {str(payload)[:200]}")

        resp = self._http.post(url, json=payload)
        print(f"[CLIENT] Response {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()

        data = resp.json()
        state = data.get("status", {}).get("state")

        if state != "completed":
            raise RuntimeError(f"Task did not complete successfully. status.state={state}")

        return data

    @staticmethod
    def extract_text(response: dict) -> str:
        """Extract first text part, or file URL if the part is a file."""
        artifacts = response.get("artifacts", [])
        for artifact in artifacts:
            for part in artifact.get("parts", []):
                if part.get("type") == "text":
                    return part.get("text", "")
                if part.get("type") == "file":
                    return part.get("file", {}).get("url", "")
        return ""