from typing import List
from unittest.mock import MagicMock

from pydantic import TypeAdapter
from starlette import status
from starlette.testclient import TestClient

from src.inventory.routes.schemas.request_models.product import ProductDataRequestModel
from src.inventory.routes.schemas.response_models.product import (
    ProductDataResponseModel,
)
from src.inventory.services.product_service import ProductService
from src.inventory.services.schemas.product_dto import ProductDTO


def test_create_product_happy_path_returns_200(client: TestClient, mocker: MagicMock):
    product = ProductDTO(sku="BLUE_CHAIR")
    mock_create_product = mocker.patch.object(
        ProductService, "create_product", return_value=product
    )
    request_data = ProductDataRequestModel(sku="BLUE_CHAIR")
    res = client.post("/product", data=request_data.model_dump_json())
    assert res.status_code == status.HTTP_200_OK
    res_data = ProductDataResponseModel.model_validate(res.json())
    assert res_data.sku == product.sku
    mock_create_product.assert_called_once_with(product=request_data)


def test_list_products_happy_path_returns_200(client: TestClient, mocker: MagicMock):
    products = [ProductDTO(sku="BLUE_CHAIR"), ProductDTO(sku="RED_CHAIR")]
    mock_get_all_products = mocker.patch.object(
        ProductService, "get_all_products", return_value=products
    )
    res = client.get("/product")
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()) == 2
    TypeAdapter(List[ProductDataResponseModel]).validate_python(
        res.json(), from_attributes=True
    )
    mock_get_all_products.assert_called_once_with()


def test_get_product_happy_path_returns_200(client: TestClient, mocker: MagicMock):
    product = ProductDTO(sku="RED_CHAIR")
    mock_get_product = mocker.patch.object(
        ProductService, "get_product", return_value=product
    )
    res = client.get("/product/RED_CHAIR")
    assert res.status_code == status.HTTP_200_OK
    ProductDataResponseModel.model_validate(res.json())
    mock_get_product.assert_called_once_with(sku="RED_CHAIR")


# TODO: test_get_product_not_found_returns_404


def test_delete_product_happy_path_returns_200(client: TestClient, mocker: MagicMock):
    mock_delete_product = mocker.patch.object(ProductService, "delete_product")
    res = client.delete("/product/RED_CHAIR")
    assert res.status_code == status.HTTP_200_OK
    assert res.json() is None
    mock_delete_product.assert_called_once_with(sku="RED_CHAIR")


# TODO: test_delete_product_not_found_returns_404
