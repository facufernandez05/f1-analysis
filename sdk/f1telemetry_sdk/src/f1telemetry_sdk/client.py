from __future__ import annotations

import httpx

from .models import IngestRequest


class F1TelemetryClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs) -> dict | list:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    def health(self) -> dict:
        return self._request("GET", "/health")

    def ingest(self, req: IngestRequest) -> dict:
        return self._request("POST", "/api/v1/ingest/", json=req.to_payload())

    def list_sessions(self) -> list[dict]:
        return self._request("GET", "/api/v1/sessions/")

    def session_stats(self, session_id: int) -> dict:
        return self._request("GET", f"/api/v1/sessions/{session_id}/stats")

    def session_pace(
        self,
        session_id: int,
        window_size: int = 3,
        normalize_to_best: bool = True,
    ) -> dict:
        return self._request(
            "GET",
            f"/api/v1/sessions/{session_id}/pace",
            params={
                "window_size": window_size,
                "normalize_to_best": str(normalize_to_best).lower(),
            },
        )
