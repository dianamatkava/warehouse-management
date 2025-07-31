import pytest
from sqlalchemy.orm import Session

from src.inventory.adapters.repository import ProductRepository


@pytest.fixture(name="product_repository")
def get_product_repository(session: Session) -> ProductRepository:
    return ProductRepository(session)
