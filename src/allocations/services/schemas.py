"""Consumes domain models, enforces business logic, and returns domain instances or slim DTOs."""

from datetime import date

from pydantic import BaseModel


class AllocationSchemaDTO(BaseModel):
    order_id: str
    sku: str
    qty: int


class BatchSchemaDTO(BaseModel):
    reference: str
    sku: str
    eta: date | None
    qty: int
