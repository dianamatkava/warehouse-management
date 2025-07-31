# The Repository pattern is an abstraction over persistent storage
from typing import List, Type

from sqlalchemy.orm import Session

from src.inventory.domain.batch_model import InventoryBatchModel
from src.inventory.domain.product_model import ProductModel
from src.shared.repository import AbstractRepository


class InventoryBatchRepository(AbstractRepository):
    session: Session

    def __init__(self, session: Session):
        self.session = session

    def get(self, reference: str) -> InventoryBatchModel:
        return (
            self.session.query(InventoryBatchModel).filter_by(reference=reference).one()
        )

    def add(self, batch: InventoryBatchModel) -> None:
        self.session.add(batch)

    def list(self) -> List[InventoryBatchModel]:
        return self.session.query(InventoryBatchModel).all()

    def delete(self, reference: str) -> None:
        self.session.query(InventoryBatchModel).filter_by(reference=reference).delete()


class ProductRepository(AbstractRepository[ProductModel]):
    session: Session

    def __init__(self, session: Session):
        self.session = session

    def get(self, sku: str) -> Type[ProductModel]:
        return self.session.query(ProductModel).filter_by(sku=sku).one()

    def add(self, product: ProductModel) -> None:
        self.session.add(product)

    def list(self) -> List[Type[ProductModel]]:
        return self.session.query(ProductModel).all()

    def delete(self, sku: str) -> None:
        self.session.query(ProductModel).filter_by(sku=sku).delete()
