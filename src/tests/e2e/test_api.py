"""
Test API that performs end-to-end testing of the API routers by verifying core domain functionality using:
 - production-like unit-of-work
 - postgres-test database and session
Also validates the REST API contract by ensuring correct response codes, error handling, and response structures.
"""
import uuid

import pytest
from sqlmodel import Session
from starlette import status
from starlette.testclient import TestClient

from src.routes.schemas.allocations import AllocationsAllocateIn, AllocationsAllocateOut, BatchesCreationModelIn
from src.services.batch_service import OutOfStock
from src.settings import get_settings

settings = get_settings()


def random_suffix():
    return uuid.uuid4().hex[:6]


def random_sku(name=""):
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name=""):
    return f"batch-{name}-{random_suffix()}"


def create_batch(ref: str, sku: str, eta: str, qty: int, client: TestClient):
    batch = BatchesCreationModelIn(ref=ref, sku=sku, eta=eta, qty=qty)
    res = client.post("/batch", content=batch.model_dump_json(), headers={"Content-Type": "application/json"})
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.usefixtures('postgres_db')
def test_happy_path_returns_201_and_allocated_batch(pg_session: Session, client: TestClient):
    ref, other_ref = random_batchref(), random_batchref('other')
    sku, other_sku = random_sku(), random_sku('other')
    create_batch(ref=ref, sku=sku, eta="2011-01-01", qty=10, client=client)
    create_batch(ref=other_ref, sku=other_sku, eta="2011-01-01", qty=10, client=client)

    order_line_1 = AllocationsAllocateIn(order_id="order_1", sku=sku, qty=10)

    res = client.post("/allocations", json=order_line_1.model_dump())
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["batch_reference"] == ref
    assert AllocationsAllocateOut.model_validate(res.json())


@pytest.mark.usefixtures('postgres_db')
def test_unhappy_path_returns_400_and_error_message(client: TestClient):
    order_line_1 = AllocationsAllocateIn(order_id="order_1", sku='sku', qty=10)

    with pytest.raises(OutOfStock):
        client.post("/allocations", json=order_line_1.model_dump())
