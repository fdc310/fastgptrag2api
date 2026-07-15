from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import (
    get_device_dataset_id,
    verify_collection_ownership,
    verify_data_ownership,
    check_collection_ownership,
    check_data_ownership,
)
from ..fastgpt_client import fastgpt_client
from ..schemas import PushDataParams, DataListParams, DataUpdate

router = APIRouter(prefix="/collections/{collection_id}/data", tags=["data"])


@router.post("/push")
async def push_data(
    body: PushDataParams,
    collection_id: str = Depends(verify_collection_ownership),
):
    payload = body.model_dump(exclude_none=True)
    payload["collectionId"] = collection_id
    return await fastgpt_client.push_data(payload)


@router.post("/list")
async def list_data(
    body: DataListParams,
    collection_id: str = Depends(verify_collection_ownership),
):
    payload = body.model_dump(exclude_none=True)
    payload["collectionId"] = collection_id
    return await fastgpt_client.list_data(payload)


@router.get("/{data_id}")
async def get_data_detail(
    data_id: str = Depends(verify_data_ownership),
):
    return await fastgpt_client.get_data_detail(data_id)


@router.put("/update")
async def update_data(
    body: DataUpdate,
    collection_id: str = Depends(verify_collection_ownership),
):
    if not body.dataId:
        raise HTTPException(status_code=400, detail="dataId is required")
    await check_data_ownership(body.dataId, collection_id)
    return await fastgpt_client.update_data(body.model_dump(exclude_none=True))


@router.delete("/{data_id}")
async def delete_data(
    data_id: str = Depends(verify_data_ownership),
):
    return await fastgpt_client.delete_data(data_id)
