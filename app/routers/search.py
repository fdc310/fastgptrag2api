from fastapi import APIRouter, Depends

from ..dependencies import get_device_dataset_id
from ..fastgpt_client import fastgpt_client
from ..schemas import SearchTestParams

router = APIRouter(prefix="/search", tags=["search"])


@router.post("")
async def search_test(
    body: SearchTestParams,
    dataset_id: str = Depends(get_device_dataset_id),
):
    payload = body.model_dump(exclude_none=True)
    payload["datasetId"] = dataset_id
    return await fastgpt_client.search_test(payload)
