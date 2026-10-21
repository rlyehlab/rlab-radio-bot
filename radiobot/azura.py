import base64
from pathlib import Path

import httpx


class AzuraClient:
    def __init__(self, base_url: str, api_key: str, station: str):
        self.station = station
        self.http = httpx.AsyncClient(
            base_url=f"{base_url}/api",
            headers={"X-API-Key": api_key},
            timeout=httpx.Timeout(300, connect=15),
        )

    async def upload(self, local_path: Path, remote_path: str) -> dict:
        """Upload a file into the station media library."""
        payload = {
            "path": remote_path,
            "file": base64.b64encode(local_path.read_bytes()).decode(),
        }
        response = await self.http.post(f"/station/{self.station}/files", json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self.http.aclose()
