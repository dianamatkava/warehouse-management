from datetime import datetime, date, timedelta
from typing import Optional

import pytest

from src.adapters.uow import UnitOfWork
from src.domain import model
from src.domain.model import BatchModel
from src.routes.schemas.allocations import AllocationsAllocateIn, OrderLineSchema
from src.services.batch_service import BatchService, OutOfStock
from src.tests.conftest import FakeRepository


class BatchFactory:

    def __init__(self, fake_repository: FakeRepository):
        self.fake_repository = fake_repository

    def for_batch(self, ref: str, sku: str, qty: int, eta: Optional[date]):
        return self.fake_repository([model.BatchModel(ref, sku, qty, eta)])


def test_batch_allocates_when_has_space(batch_service: BatchService, fake_uof: UnitOfWork):
    sku = "BLUE_VASE"
    batch_1 = model.BatchModel('batch1', sku=sku, eta=datetime.strptime("2011-01-01", "%Y-%m-%d"), qty=10)
    batch_2 = model.BatchModel('batch2', sku=sku, eta=datetime.strptime("2011-01-10", "%Y-%m-%d"), qty=10)

    fake_uof.batch_repo.build([batch_1, batch_2])

    order_line_1 = AllocationsAllocateIn(order_id="order_1", sku=sku, qty=10)
    order_line_2 = AllocationsAllocateIn(order_id="order_2", sku=sku, qty=10)

    res = batch_service.allocate(order_line_1)
    assert res == batch_1.reference
    assert batch_service.uof.session.committed is True

    res = batch_service.allocate(order_line_2)
    assert res == batch_2.reference

    with pytest.raises(OutOfStock):
        batch_service.allocate(order_line_2)


def test_prefers_current_stock_batches_to_shipments(batch_service: BatchService, fake_repository: FakeRepository):
    in_stock_batch = BatchModel("1", "BLUE-VASE", qty=100, eta=None)
    shipment_batch = BatchModel("2", "BLUE-VASE", qty=100, eta=date.today())
    fake_repository.build([in_stock_batch, shipment_batch])

    line = AllocationsAllocateIn(order_id='1', sku="BLUE-VASE", qty=10)
    batch_service.allocate(line)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches(batch_service: BatchService, fake_repository: FakeRepository):
    earlier = BatchModel("1", "BLUE-VASE", qty=100, eta=date.today())
    medium = BatchModel("1", "BLUE-VASE", qty=100, eta=date.today() + timedelta(days=2))
    latest = BatchModel("2", "BLUE-VASE", qty=100, eta=date.today() + timedelta(days=4))
    fake_repository.build([earlier, medium, latest])

    line = AllocationsAllocateIn(order_id='1', sku="BLUE-VASE", qty=10)
    batch_service.allocate(line)

    assert earlier.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref(batch_service: BatchService, fake_repository: FakeRepository):
    in_stock_batch = BatchModel("1", "BLUE-VASE", qty=100, eta=None)
    shipment_batch = BatchModel("2", "BLUE-VASE", qty=100, eta=date.today())
    fake_repository.build([in_stock_batch, shipment_batch])

    line = AllocationsAllocateIn(order_id='1', sku="BLUE-VASE", qty=10)
    allocation = batch_service.allocate(line)

    assert allocation == in_stock_batch.reference


def test_raises_out_of_stock_exception_if_cannot_allocate(batch_service: BatchService, fake_repository: FakeRepository):
    batch = BatchModel("1", "BLUE-VASE", qty=10, eta=None)
    fake_repository.build([batch])

    order_line = AllocationsAllocateIn(order_id='1', sku="BLUE-VASE", qty=10)
    batch_service.allocate(order_line)

    with pytest.raises(OutOfStock):
        batch_service.allocate(AllocationsAllocateIn(order_id='1', sku="BLUE-VASE", qty=1))


def test_returns_batches_with_allocations(batch_service: BatchService, fake_repository: FakeRepository):
    batch_1 = BatchModel("1", "BLUE-VASE", qty=100, eta=date.today())
    batch_2 = BatchModel("2", "RED_CHAIR", qty=100, eta=date.today() + timedelta(days=2))
    fake_repository.build([batch_1, batch_2])

    line_1 = AllocationsAllocateIn(order_id='1', sku="BLUE-VASE", qty=10)
    line_2 = AllocationsAllocateIn(order_id='2', sku="BLUE-VASE", qty=30)
    batch_service.allocate(line_1)
    batch_service.allocate(line_2)

    batches = batch_service.get_allocations()
    batches.items.sort(key=lambda x: x.reference)

    assert batches.total == 2
    assert len(batches.items) == 2

    assert batches.items[0].reference == batch_1.reference
    assert batches.items[0].sku == batch_1.sku
    assert batches.items[0].eta == batch_1.eta
    assert batches.items[0].available_quantity == batch_1.available_quantity
    assert batches.items[0].allocated_quantity == batch_1.allocated_quantity
    assert batches.items[0].allocations == [
        OrderLineSchema(**line_1.model_dump()),
        OrderLineSchema(**line_2.model_dump())
    ]

    assert batches.items[1].reference == batch_2.reference
    assert batches.items[1].sku == batch_2.sku
    assert batches.items[1].eta == batch_2.eta
    assert batches.items[1].available_quantity == batch_2.available_quantity
    assert batches.items[1].allocated_quantity == batch_2.allocated_quantity
    assert batches.items[1].allocations == []
