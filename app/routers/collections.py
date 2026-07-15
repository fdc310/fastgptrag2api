from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_device_dataset_id, verify_collection_ownership, check_collection_ownership
from ..fastgpt_client import fastgpt_client
from ..schemas import CollectionListParams, CollectionUpdate

router = APIRouter(prefix="/collections", tags=["collection"])


@router.post("/list")
async def list_collections(
    body: CollectionListParams,
    dataset_id: str = Depends(get_device_dataset_id),
):
    payload = body.model_dump(exclude_none=True)
    payload["datasetId"] = dataset_id
    return await fastgpt_client.list_collections(payload)


@router.get("/{collection_id}")
async def get_collection_detail(
    collection_id: str = Depends(verify_collection_ownership),
):
    return await fastgpt_client.get_collection_detail(collection_id)


@router.post("/update")
async def update_collection(
    body: CollectionUpdate,
    dataset_id: str = Depends(get_device_dataset_id),
):
    if body.id is None and body.externalFileId is None:
        raise HTTPException(status_code=400, detail="Either id or externalFileId is required")

    if body.id is not None:
        await check_collection_ownership(body.id, dataset_id)

    payload = body.model_dump(exclude_none=True)
    if body.id is None and body.externalFileId:
        payload["datasetId"] = dataset_id
    return await fastgpt_client.update_collection(payload)
