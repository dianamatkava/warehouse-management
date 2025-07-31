from datetime import date

from pydantic import BaseModel


class InventoryBatchDTO(BaseModel):
    reference: str
    sku: str
    eta: date | None
    qty: int  # initial quantity
