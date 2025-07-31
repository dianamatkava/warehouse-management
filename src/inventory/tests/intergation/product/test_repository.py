from contextlib import nullcontext

import pytest
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session

from src.inventory.adapters.repository import ProductRepository
from src.inventory.domain.product_model import ProductModel


def create_product(session: Session, sku: str):
    session.add(ProductModel(sku=sku))
    session.commit()


def test_repository_can_get_product(
    session: Session, product_repository: ProductRepository
):
    sku = "BLUE_CHAIR"
    create_product(session=session, sku=sku)

    product = product_repository.get(sku=sku)
    assert product.sku == sku


def test_repository_can_get_product_not_found(product_repository: ProductRepository):
    with pytest.raises(NoResultFound):
        product_repository.get(sku="BLUE_CHAIR")


def test_repository_can_list_products(
    session: Session, product_repository: ProductRepository
):
    products_sku = ["BLUE_CHAIR", "RED_CHAIR"]
    for sku in products_sku:
        create_product(session=session, sku=sku)

    products = product_repository.list()
    assert len(products) == 2
    assert sorted(products_sku) == sorted([product.sku for product in products])


def test_repository_can_list_products_when_empty(product_repository: ProductRepository):
    products = product_repository.list()
    assert products == []


def test_repository_create_products(
    session: Session, product_repository: ProductRepository
):
    sku = "RED_CHAIR"
    product_repository.add(ProductModel(sku=sku))
    assert session.query(ProductModel).filter_by(sku=sku).one()


def test_repository_delete_product(
    session: Session, product_repository: ProductRepository
):
    products_sku = ["BLUE_CHAIR", "RED_CHAIR"]
    for sku in products_sku:
        create_product(session=session, sku=sku)

    product_repository.delete(sku="BLUE_CHAIR")

    products = session.query(ProductModel).all()
    assert len(products) == 1
    assert products[0].sku == "RED_CHAIR"


def test_repository_delete_product_when_not_found(
    session: Session, product_repository: ProductRepository
):
    with nullcontext():
        product_repository.delete(sku="BLUE_CHAIR")
