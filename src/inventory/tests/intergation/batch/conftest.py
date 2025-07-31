import pytest
from sqlalchemy.orm import Session

from src.inventory.adapters.repository import InventoryBatchRepository


@pytest.fixture(name="batch_repository")
def get_batch_repository(session: Session) -> InventoryBatchRepository:
    return InventoryBatchRepository(session)
