import logging
import secrets
import time
from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db
from .models import SettingRobot, MemberRobotAttributes
from .fastgpt_client import fastgpt_client

logger = logging.getLogger(__name__)

# --- in-memory cache for device_name -> dataset_id ---
_CACHE_TTL = 300
_dataset_cache: dict[str, tuple[str, float]] = {}


def _cache_get(key: str) -> str | None:
    entry = _dataset_cache.get(key)
    if entry is None:
        return None
    dataset_id, expire_at = entry
    if time.monotonic() > expire_at:
        _dataset_cache.pop(key, None)
        return None
    return dataset_id


def _cache_set(key: str, dataset_id: str) -> None:
    _dataset_cache[key] = (dataset_id, time.monotonic() + _CACHE_TTL)


async def verify_api_key(authorization: str | None = Header(default=None, alias="Authorization")) -> None:
    """Validate the caller's API key against the one configured in .env."""
    if not settings.api_key:
        raise HTTPException(status_code=500, detail="API_KEY not configured on server")
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    expected = f"Bearer {settings.api_key}"
    if not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


async def get_device_dataset_id(
    x_device_name: str = Header(..., alias="X-Device-Name"),
    _auth: None = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Resolve the latest active FastGPT dataset_id for a given device name.

    Joins ya_setting_robot (by device_name) with ya_member_robot_attributes (by robot_id),
    filters out deleted records on both sides, takes the last row by id DESC.
    Results are cached in memory for 5 minutes.
    """
    cached = _cache_get(x_device_name)
    if cached is not None:
        logger.debug("cache hit  device=%s dataset_id=%s", x_device_name, cached)
        return cached

    t0 = time.monotonic()
    result = await db.execute(
        select(MemberRobotAttributes.dataset_id, MemberRobotAttributes.member_id)
        .join(SettingRobot, MemberRobotAttributes.robot_id == SettingRobot.id)
        .where(
            SettingRobot.device_name == x_device_name,
            SettingRobot.is_delete == 0,
            MemberRobotAttributes.is_delete == 0,
        )
        .order_by(MemberRobotAttributes.id.desc())
        .limit(1)
    )
    row = result.first()
    elapsed = round((time.monotonic() - t0) * 1000)
    if row is None:
        logger.warning("device=%s not found or disabled | db=%sms", x_device_name, elapsed)
        raise HTTPException(status_code=404, detail="No active dataset found for this device name")
    if not row.dataset_id:
        logger.warning("device=%s has no dataset_id bound | db=%sms", x_device_name, elapsed)
        raise HTTPException(status_code=404, detail="Device has no dataset_id bound")

    logger.info("device=%s resolved to dataset_id=%s | db=%sms", x_device_name, row.dataset_id, elapsed)
    _cache_set(x_device_name, row.dataset_id)
    return row.dataset_id


async def check_collection_ownership(collection_id: str, dataset_id: str) -> None:
    """Verify that the collection belongs to the given dataset. Raises HTTPException on mismatch."""
    try:
        detail = await fastgpt_client.get_collection_detail(collection_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("failed to verify collection ownership | collection=%s | %s", collection_id, exc)
        raise HTTPException(status_code=502, detail="Failed to verify collection ownership")

    col_dataset_id = detail.get("datasetId") if isinstance(detail, dict) else None
    if col_dataset_id != dataset_id:
        logger.warning(
            "collection ownership mismatch | collection=%s expected_dataset=%s got_dataset=%s",
            collection_id, dataset_id, col_dataset_id,
        )
        raise HTTPException(status_code=403, detail="Collection does not belong to this device")


async def check_data_ownership(data_id: str, collection_id: str) -> None:
    """Verify that the data belongs to the given collection. Raises HTTPException on mismatch."""
    try:
        detail = await fastgpt_client.get_data_detail(data_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("failed to verify data ownership | data=%s | %s", data_id, exc)
        raise HTTPException(status_code=502, detail="Failed to verify data ownership")

    data_collection_id = detail.get("collectionId") if isinstance(detail, dict) else None
    if data_collection_id != collection_id:
        logger.warning(
            "data ownership mismatch | data=%s expected_collection=%s got_collection=%s",
            data_id, collection_id, data_collection_id,
        )
        raise HTTPException(status_code=403, detail="Data does not belong to this collection")


async def verify_collection_ownership(
    collection_id: str,
    dataset_id: str = Depends(get_device_dataset_id),
) -> str:
    """Path-parameter based ownership check. Returns collection_id on success."""
    await check_collection_ownership(collection_id, dataset_id)
    return collection_id


async def verify_data_ownership(
    data_id: str,
    collection_id: str = Depends(verify_collection_ownership),
) -> str:
    """Path-parameter based ownership check. Returns data_id on success."""
    await check_data_ownership(data_id, collection_id)
    return data_id
