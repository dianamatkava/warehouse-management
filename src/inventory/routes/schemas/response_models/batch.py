from datetime import date
from typing import Annotated

from pydantic import Field

from src.allocations.services.schemas import BatchSchemaDTO


class BatchesListResponseModel(BatchSchemaDTO):
    """Model represent list of batches."""

    reference: Annotated[str, Field(description="Batch unique ID.")]
    sku: Annotated[str, Field(description="SKU (Stock Keeping Unit) of the product.")]
    eta: Annotated[
        date | None,
        Field(
            description="ETA ((Estimated Time of Arrival). Batches have an ETA if they are currently shipping. We allocate to shipment batches in order of which has the earliest ETA."
        ),
    ]
    qty: Annotated[
        int, Field(description="Quantity of the product available in the batch.")
    ]
