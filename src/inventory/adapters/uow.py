from typing import Self, Type

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.inventory.adapters.repository import (
    InventoryBatchRepository,
    ProductRepository,
)
from src.settings import get_settings
from src.shared.repository import AbstractRepository
from src.shared.uow import AbstractUnitOfWork

settings = get_settings()

DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(settings.DB_URL))


class InventoryBatchUnitOfWork(AbstractUnitOfWork):
    """
    Context Manager for adapters operations.
    The Unit of Work pattern manages adapters changes as a single atomic transaction.
    Manages session life cycle.
    """

    batch_repo: InventoryBatchRepository

    def __init__(
        self,
        session_factory=DEFAULT_SESSION_FACTORY,
        batch_repo: Type[AbstractRepository] = InventoryBatchRepository,
    ):
        self.session_factory = session_factory
        self.batch_repo_cls = batch_repo

    def __enter__(self) -> Self:
        self.session: Session = self.session_factory()
        self.batch_repo = self.batch_repo_cls(session=self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)

    def rollback(self):
        self.session.rollback()

    def commit(self):
        self.session.commit()


class ProductUnitOfWork(AbstractUnitOfWork):
    """
    Context Manager for adapters operations.
    The Unit of Work pattern manages adapters changes as a single atomic transaction.
    Manages session life cycle.
    """

    product_repo: ProductRepository

    def __init__(
        self,
        session_factory=DEFAULT_SESSION_FACTORY,
        product_repo: AbstractRepository = ProductRepository,
    ):
        self.session_factory = session_factory
        self.product_repo_cls = product_repo

    def __enter__(self) -> Self:
        self.session: Session = self.session_factory()
        self.product_repo = self.product_repo_cls(session=self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)

    def rollback(self):
        self.session.rollback()

    def commit(self):
        self.session.commit()
