import logging
import time

import httpx
from fastapi import HTTPException

from .config import settings

logger = logging.getLogger(__name__)


class FastGPTClient:
    """FastGPT knowledge base OpenAPI wrapper"""

    def _check_response(self, r: httpx.Response, *, endpoint: str) -> dict:
        """Return parsed JSON on 2xx; on failure, propagate the upstream error
        as an HTTPException so callers see the real status and detail."""
        if r.is_success:
            return r.json()
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        logger.warning(
            "fastgpt error | %s %s → %s | %s",
            r.request.method, endpoint, r.status_code, str(detail)[:200],
        )
        raise HTTPException(status_code=r.status_code, detail=detail)

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        c = await self.get_client()
        t0 = time.monotonic()
        r = await c.request(method, endpoint, **kwargs)
        elapsed = round((time.monotonic() - t0) * 1000)
        logger.debug("fastgpt | %s %s → %s | %sms", method, endpoint, r.status_code, elapsed)
        return self._check_response(r, endpoint=endpoint)

    def __init__(self):
        self.base_url = settings.fastgpt_base_url.rstrip("/")
        self.api_key = settings.fastgpt_api_key
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ---- training usage ----

    async def create_training_usage(self, body: dict) -> dict:
        return await self._request("POST", "/api/support/wallet/usage/createTrainingUsage", json=body)

    # ---- dataset ----

    async def create_dataset(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/create", json=body)

    async def list_datasets(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/list", json=body)

    async def get_dataset_detail(self, dataset_id: str) -> dict:
        return await self._request("GET", "/api/core/dataset/detail", params={"id": dataset_id})

    async def delete_dataset(self, dataset_id: str) -> dict:
        return await self._request("DELETE", "/api/core/dataset/delete", params={"id": dataset_id})

    # ---- collection ----

    async def create_collection(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/collection/create", json=body)

    async def create_text_collection(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/collection/create/text", json=body)

    async def create_link_collection(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/collection/create/link", json=body)

    async def create_local_file_collection(self, file_bytes: bytes, filename: str, data_json: str) -> dict:
        c = await self.get_client()
        t0 = time.monotonic()
        endpoint = "/api/core/dataset/collection/create/localFile"
        r = await c.post(
            endpoint,
            files={"file": (filename, file_bytes)},
            data={"data": data_json},
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        elapsed = round((time.monotonic() - t0) * 1000)
        logger.debug("fastgpt | POST %s → %s | %sms", endpoint, r.status_code, elapsed)
        return self._check_response(r, endpoint=endpoint)

    async def create_api_collection(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/collection/create/apiCollection", json=body)

    async def create_external_file_collection(self, body: dict) -> dict:
        return await self._request("POST", "/api/proApi/core/dataset/collection/create/externalFileUrl", json=body)

    async def list_collections(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/collection/listV2", json=body)

    async def get_collection_detail(self, collection_id: str) -> dict:
        return await self._request("GET", "/api/core/dataset/collection/detail", params={"id": collection_id})

    async def update_collection(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/collection/update", json=body)

    async def delete_collection(self, body: dict) -> dict:
        return await self._request("DELETE", "/api/core/dataset/collection/delete", json=body)

    # ---- data ----

    async def push_data(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/data/pushData", json=body)

    async def list_data(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/data/v2/list", json=body)

    async def get_data_detail(self, data_id: str) -> dict:
        return await self._request("GET", "/api/core/dataset/data/detail", params={"id": data_id})

    async def update_data(self, body: dict) -> dict:
        return await self._request("PUT", "/api/core/dataset/data/update", json=body)

    async def delete_data(self, data_id: str) -> dict:
        return await self._request("DELETE", "/api/core/dataset/data/delete", params={"id": data_id})

    # ---- search ----

    async def search_test(self, body: dict) -> dict:
        return await self._request("POST", "/api/core/dataset/searchTest", json=body)


fastgpt_client = FastGPTClient()
