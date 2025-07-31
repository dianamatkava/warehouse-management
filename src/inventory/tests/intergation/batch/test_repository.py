from contextlib import nullcontext
from datetime import date

import pytest
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session

from src.inventory.adapters.repository import InventoryBatchRepository
from src.inventory.domain.batch_model import InventoryBatchModel


def create_batch(
    session: Session,
    reference: str,
    sku: str = "BLUE_CHAIR",
    qty: int = 20,
    eta: date = None,
):
    batch = InventoryBatchModel(reference=reference, sku=sku, eta=eta, qty=qty)
    session.add(batch)
    session.commit()
    return batch


def test_repository_can_get_batch(
    session: Session, batch_repository: InventoryBatchRepository
):
    reference = "BATCH-001"
    create_batch(session=session, reference=reference)

    batch = batch_repository.get(reference=reference)
    assert batch.reference == reference
    assert batch.sku == "BLUE_CHAIR"
    assert batch._purchased_quantity == 20


def test_repository_can_get_batch_not_found(batch_repository: InventoryBatchRepository):
    with pytest.raises(NoResultFound):
        batch_repository.get(reference="BATCH-001")


def test_repository_can_list_batches(
    session: Session, batch_repository: InventoryBatchRepository
):
    batch_refs = ["BATCH-001", "BATCH-002"]
    for ref in batch_refs:
        create_batch(session=session, reference=ref, sku=f"CHAIR-{ref}")

    batches = batch_repository.list()
    assert len(batches) == 2
    assert sorted(batch_refs) == sorted([batch.reference for batch in batches])


def test_repository_can_list_batches_when_empty(
    batch_repository: InventoryBatchRepository,
):
    batches = batch_repository.list()
    assert batches == []


def test_repository_create_batch(
    session: Session, batch_repository: InventoryBatchRepository
):
    reference = "BATCH-001"
    batch = InventoryBatchModel(
        reference=reference, sku="RED_CHAIR", eta=date(2024, 1, 15), qty=25
    )

    batch_repository.add(batch)

    # Verify it was added to the session
    retrieved_batch = (
        session.query(InventoryBatchModel).filter_by(reference=reference).one()
    )
    assert retrieved_batch.reference == reference
    assert retrieved_batch.sku == "RED_CHAIR"
    assert retrieved_batch._purchased_quantity == 25


def test_repository_create_batch_without_eta(
    session: Session, batch_repository: InventoryBatchRepository
):
    reference = "BATCH-001"
    batch = InventoryBatchModel(reference=reference, sku="BLUE_CHAIR", eta=None, qty=30)

    batch_repository.add(batch)

    retrieved_batch = (
        session.query(InventoryBatchModel).filter_by(reference=reference).one()
    )
    assert retrieved_batch.reference == reference
    assert retrieved_batch.eta is None


def test_repository_delete_batch(
    session: Session, batch_repository: InventoryBatchRepository
):
    batch_refs = ["BATCH-001", "BATCH-002"]
    for ref in batch_refs:
        create_batch(session=session, reference=ref)

    batch_repository.delete(reference="BATCH-001")

    batches = session.query(InventoryBatchModel).all()
    assert len(batches) == 1
    assert batches[0].reference == "BATCH-002"


def test_repository_delete_batch_when_not_found(
    session: Session, batch_repository: InventoryBatchRepository
):
    with nullcontext():
        batch_repository.delete(reference="BATCH-001")


def test_repository_with_different_skus(
    session: Session, batch_repository: InventoryBatchRepository
):
    create_batch(session=session, reference="BATCH-001", sku="BLUE_CHAIR", qty=10)
    create_batch(session=session, reference="BATCH-002", sku="RED_CHAIR", qty=15)
    create_batch(session=session, reference="BATCH-003", sku="BLUE_CHAIR", qty=20)

    batches = batch_repository.list()
    assert len(batches) == 3

    blue_chair_batches = [b for b in batches if b.sku == "BLUE_CHAIR"]
    assert len(blue_chair_batches) == 2
    assert sum(b._purchased_quantity for b in blue_chair_batches) == 30


def test_repository_with_eta_dates(
    session: Session, batch_repository: InventoryBatchRepository
):
    eta1 = date(2024, 1, 15)
    eta2 = date(2024, 2, 20)

    create_batch(session=session, reference="BATCH-001", eta=eta1)
    create_batch(session=session, reference="BATCH-002", eta=eta2)
    create_batch(session=session, reference="BATCH-003", eta=None)

    batches = batch_repository.list()
    assert len(batches) == 3

    batches_with_eta = [b for b in batches if b.eta is not None]
    assert len(batches_with_eta) == 2

    batch_001 = next(b for b in batches if b.reference == "BATCH-001")
    assert batch_001.eta == eta1
