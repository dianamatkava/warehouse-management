from datetime import date
from typing import Optional

from sqlmodel import Session

from src.adapters.repository import BatchRepository
from src.adapters.uow import AbstractUnitOfWork
from src.domain import model
from src.routes.schemas.allocations import AllocationsAllocateIn, AllocationsListOut
from src.services.transformers.batch_service import transform_batch_to_batch_schema


class OutOfStock(Exception):
    """OutOfStock Exception"""


class BatchService:

    uof: AbstractUnitOfWork

    def __init__(self, uof: AbstractUnitOfWork):
        self.uof = uof

    def add_batch(self, ref: str, sku: str, qty: int, eta: Optional[date]) -> None:
        with self.uof as uof:
            uof.batch_repo.add(model.BatchModel(ref, sku, qty, eta))
            uof.commit()

    def get_allocations(self) -> AllocationsListOut:
        with self.uof as uof:
            batches = uof.batch_repo.list()
        return AllocationsListOut(items=[transform_batch_to_batch_schema(b) for b in batches], total=len(batches), offset=10)

    def allocate(self, order_line: AllocationsAllocateIn) -> str:
        with self.uof as uof:
            order_line = model.OrderLineModel(**order_line.model_dump())
            batches = uof.batch_repo.list()
            try:
                batch = next(b for b in sorted(batches) if b.can_allocate(order_line))
            except StopIteration as e:
                print(f"Error allocating batches: {e}")
                raise OutOfStock() from e

            batch.allocate(order_line)
            uof.commit()
        return batch.reference

    def deallocate(self, order_line, batch_reference: str):
        with self.uof as uof:
            batch = uof.batch_repo.get(batch_reference)
            batch.deallocate(order_line)
            uof.commit()


