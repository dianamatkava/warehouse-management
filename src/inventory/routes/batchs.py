from typing import Annotated, List

from fastapi import APIRouter, Path
from fastapi import Depends, Body
from pydantic import TypeAdapter
from starlette import status

from src.allocations.services.schemas import BatchSchemaDTO
from src.inventory.conf import get_batch_service
from src.inventory.routes.schemas.request_models.batch import (
    BatchesCreationModelRequestModel,
)
from src.inventory.routes.schemas.response_models.batch import BatchesListResponseModel
from src.inventory.services.batch_service import BatchService

router = APIRouter(prefix="/batch", tags=["batch"])


@router.get(
    "", status_code=status.HTTP_200_OK, response_model=List[BatchesListResponseModel]
)
def get_batches(
    batch_service: Annotated[BatchService, Depends(get_batch_service)],
) -> List[BatchesListResponseModel]:
    """
    Lists all available batches in the system.
    Returns an empty list if no batches are found.
    """
    return TypeAdapter(List[BatchesListResponseModel]).validate_python(
        batch_service.get_batches(), from_attributes=True
    )


@router.get("/{ref}", status_code=status.HTTP_200_OK, response_model=BatchSchemaDTO)
def get_batch(
    ref: Annotated[
        str, Path(..., description="The reference of the batch to retrieve")
    ],
    batch_service: Annotated[BatchService, Depends(get_batch_service)],
) -> BatchSchemaDTO:
    """
    Retrieves a single batch by its reference.
    Will return 404 if the batch is not found.
    """
    return TypeAdapter(BatchSchemaDTO).validate_python(
        batch_service.get_batche_by_ref(ref), from_attributes=True
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=None)
def add_batch(
    body: Annotated[
        BatchesCreationModelRequestModel,
        Body(..., description="The batch details to create"),
    ],
    batch_service: Annotated[BatchService, Depends(get_batch_service)],
) -> None:
    """
    Creates a new batch in the inventory system.
    If a batch with the same reference already exists, it will be rejected.
    """
    batch_service.add_batch(ref=body.ref, sku=body.sku, qty=body.qty, eta=body.eta)


@router.delete("/{ref}", status_code=status.HTTP_200_OK, response_model=None)
def delete_batch(
    ref: Annotated[str, Path(..., description="The reference of the batch to delete")],
    batch_service: Annotated[BatchService, Depends(get_batch_service)],
) -> None:
    """
    Permanently removes a batch from the system.
    Will return 404 if the batch is not found.
    The operation cannot be undone.
    """
    batch_service.delete_batch(ref)
