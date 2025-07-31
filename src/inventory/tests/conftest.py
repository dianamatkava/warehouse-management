from typing import Type, List

import pytest

from src.inventory.adapters.uow import ProductUnitOfWork, InventoryBatchUnitOfWork
from src.inventory.domain.product_model import ProductModel
from src.inventory.domain.batch_model import InventoryBatchModel
from src.inventory.services.product_service import ProductService
from src.inventory.services.batch_service import BatchService
from src.shared.repository import AbstractRepository
from src.shared.uow import AbstractUnitOfWork


class FakeProductRepository(AbstractRepository):
    def __init__(self, products=(), *args, **kwargs):
        self._products = set(products)

    def build(self, products: List[ProductModel]) -> None:
        self._products = set(products)

    def add(self, product: ProductModel) -> None:
        self._products.add(product)

    def get(self, sku) -> None:
        return next(b for b in self._products if b.sku == sku)

    def list(self) -> List[ProductModel]:
        return list(self._products)

    def delete(self, sku) -> None:
        product = next(b for b in self._products if b.sku == sku)
        self._products.remove(product)


class FakeBatchRepository(AbstractRepository):
    def __init__(self, batches=(), *args, **kwargs):
        self._batches = set(batches)

    def build(self, batches: List[InventoryBatchModel]) -> None:
        self._batches = set(batches)

    def add(self, batch: InventoryBatchModel) -> None:
        self._batches.add(batch)

    def get(self, reference: str) -> InventoryBatchModel:
        return next(b for b in self._batches if b.reference == reference)

    def list(self) -> List[InventoryBatchModel]:
        return list(self._batches)

    def delete(self, reference: str) -> None:
        batch = next(b for b in self._batches if b.reference == reference)
        self._batches.remove(batch)


class FakeProductUnitOfWork(AbstractUnitOfWork):
    committed: bool | None = False
    product_repo: Type[AbstractRepository]  # type: ignore

    def __init__(
        self, product_repo: AbstractRepository = FakeProductRepository
    ) -> None:
        self.product_repo = product_repo

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.committed = None


class FakeBatchUnitOfWork(AbstractUnitOfWork):
    committed: bool | None = False
    batch_repo: Type[AbstractRepository]  # type: ignore

    def __init__(self, batch_repo: AbstractRepository = FakeBatchRepository) -> None:
        self.batch_repo = batch_repo

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.committed = None


@pytest.fixture(name="fake_product_repo")
def get_fake_product_repo() -> FakeProductRepository:
    return FakeProductRepository()


@pytest.fixture(name="fake_batch_repo")
def get_fake_batch_repo() -> FakeBatchRepository:
    return FakeBatchRepository()


@pytest.fixture(name="fake_product_uow")
def get_fake_product_uow(
    fake_product_repo: FakeProductRepository,
) -> FakeProductUnitOfWork:
    return FakeProductUnitOfWork(product_repo=fake_product_repo)


@pytest.fixture(name="fake_batch_uow")
def get_fake_batch_uow(fake_batch_repo: FakeBatchRepository) -> FakeBatchUnitOfWork:
    return FakeBatchUnitOfWork(batch_repo=fake_batch_repo)


@pytest.fixture(name="product_service")
def get_product_service(fake_product_uow: ProductUnitOfWork) -> ProductService:
    return ProductService(uow=fake_product_uow)


@pytest.fixture(name="batch_service")
def get_batch_service(fake_batch_uow: InventoryBatchUnitOfWork) -> BatchService:
    return BatchService(uow=fake_batch_uow)
