from datetime import date

from src.inventory.domain.batch_model import InventoryBatchModel
from src.inventory.services.batch_service import BatchService
from src.inventory.tests.conftest import FakeBatchRepository


def test_add_batch(batch_service: BatchService):
    batch_service.add_batch(
        ref="BATCH-001", sku="BLUE_CHAIR", qty=20, eta=date(2024, 1, 15)
    )

    assert batch_service.uow.committed is True


def test_add_batch_with_optional_eta(batch_service: BatchService):
    batch_service.add_batch(ref="BATCH-001", sku="BLUE_CHAIR", qty=20)

    assert batch_service.uow.committed is True


def test_get_batch_by_ref_returns_batch(
    batch_service: BatchService, fake_batch_repo: FakeBatchRepository
):
    batch = InventoryBatchModel(
        reference="BATCH-001", sku="BLUE_CHAIR", eta=date(2024, 1, 15), qty=20
    )
    fake_batch_repo.build([batch])

    result = batch_service.get_batche_by_ref("BATCH-001")

    assert result.reference == batch.reference
    assert result.sku == batch.sku
    assert result.qty == batch._purchased_quantity
    assert result.eta == batch.eta


def test_get_all_batches(
    batch_service: BatchService, fake_batch_repo: FakeBatchRepository
):
    batches = [
        InventoryBatchModel(
            reference="BATCH-001", sku="BLUE_CHAIR", eta=date(2024, 1, 15), qty=20
        ),
        InventoryBatchModel(
            reference="BATCH-002", sku="RED_CHAIR", eta=date(2024, 1, 20), qty=15
        ),
    ]
    fake_batch_repo.build(batches)

    result = batch_service.get_batches()

    assert len(result) == 2
    assert sorted([batch.reference for batch in batches]) == sorted(
        [b.reference for b in result]
    )


def test_get_all_batches_returns_empty_list(batch_service: BatchService):
    result = batch_service.get_batches()
    assert result == []


def test_delete_batch(
    batch_service: BatchService, fake_batch_repo: FakeBatchRepository
):
    batch = InventoryBatchModel(
        reference="BATCH-001", sku="BLUE_CHAIR", eta=date(2024, 1, 15), qty=20
    )
    fake_batch_repo.build([batch])

    batch_service.delete_batch("BATCH-001")

    assert batch_service.uow.committed is True
    assert len(fake_batch_repo.list()) == 0


# TODO: def test_get_batch_not_found(batch_service: BatchService):
# TODO: def test_delete_batch_not_found(batch_service: BatchService):
