from src.inventory.domain.product_model import ProductModel
from src.inventory.services.product_service import ProductService
from src.inventory.services.schemas.product_dto import ProductDTO
from src.inventory.tests.conftest import FakeProductRepository


def test_create_product(product_service: ProductService):
    product_data = ProductDTO(sku="BLUE_CHAIR")
    res = product_service.create_product(product_data)

    assert product_service.uow.committed is True
    assert res == product_data


def test_get_product_returns_product(
    product_service: ProductService, fake_product_repo: FakeProductRepository
):
    product = ProductModel(sku="BLUE_CHAIR")
    fake_product_repo.build([product])

    res = product_service.get_product(product.sku)
    assert res.sku == product.sku


# TODO: def test_get_product_not_found(product_service: ProductService):


def test_get_all_products(
    product_service: ProductService, fake_product_repo: FakeProductRepository
):
    products = [ProductModel(sku="BLUE_CHAIR"), ProductModel(sku="RED_CHAIR")]
    fake_product_repo.build(products)

    res = product_service.get_all_products()

    assert len(res) == 2
    assert sorted([product.sku for product in products]) == sorted([p.sku for p in res])


def test_get_all_products_returns_empty_list(
    product_service: ProductService, fake_product_repo: FakeProductRepository
):
    res = product_service.get_all_products()
    assert res == []


def test_delete_product(
    product_service: ProductService, fake_product_repo: FakeProductRepository
):
    product = ProductModel(sku="BLUE_CHAIR")
    fake_product_repo.build([product])

    product_service.delete_product(product.sku)
    assert product_service.uow.committed is True
    assert len(fake_product_repo.list()) == 0
