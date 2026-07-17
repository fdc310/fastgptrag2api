from fastapi import APIRouter, Depends

from ..dependencies import get_device_dataset_id
from ..fastgpt_client import fastgpt_client

router = APIRouter(prefix="/datasets", tags=["dataset"])


@router.get("")
async def get_dataset_detail(
    dataset_id: str = Depends(get_device_dataset_id),
):
    """Get the dataset detail for the device resolved from the AES token."""
    return await fastgpt_client.get_dataset_detail(dataset_id)
