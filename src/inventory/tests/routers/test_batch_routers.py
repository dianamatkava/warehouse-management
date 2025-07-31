from datetime import date
from unittest.mock import MagicMock

from starlette import status
from starlette.testclient import TestClient

from src.allocations.services.schemas import BatchSchemaDTO
from src.inventory.routes.schemas.request_models.batch import (
    BatchesCreationModelRequestModel,
)
from src.inventory.services.batch_service import BatchService


def test_add_batch_happy_path_returns_201(client: TestClient, mocker: MagicMock):
    mock_add_batch = mocker.patch.object(BatchService, "add_batch")
    request_data = BatchesCreationModelRequestModel(
        ref="BATCH-001", sku="BLUE_CHAIR", qty=20, eta=date(2024, 1, 15)
    )

    res = client.post("/batch", data=request_data.model_dump_json())

    assert res.status_code == status.HTTP_201_CREATED
    assert res.json() is None
    mock_add_batch.assert_called_once_with(
        ref="BATCH-001", sku="BLUE_CHAIR", qty=20, eta=date(2024, 1, 15)
    )


def test_add_batch_without_eta_returns_201(client: TestClient, mocker: MagicMock):
    mock_add_batch = mocker.patch.object(BatchService, "add_batch")
    request_data = BatchesCreationModelRequestModel(
        ref="BATCH-001", sku="BLUE_CHAIR", qty=20, eta=None
    )

    res = client.post("/batch", json=request_data.model_dump())

    assert res.status_code == status.HTTP_201_CREATED
    assert res.json() is None
    mock_add_batch.assert_called_once_with(
        ref="BATCH-001", sku="BLUE_CHAIR", qty=20, eta=None
    )


def test_add_batch_with_valid_data_validates_request_model(
    client: TestClient, mocker: MagicMock
):
    mock_add_batch = mocker.patch.object(BatchService, "add_batch")

    # Test with all required fields
    request_data = {
        "ref": "BATCH-001",
        "sku": "BLUE_CHAIR",
        "qty": 20,
        "eta": "2024-01-15",
    }

    res = client.post("/batch", json=request_data)

    assert res.status_code == status.HTTP_201_CREATED
    mock_add_batch.assert_called_once()


def test_get_batches_happy_path_returns_200(client: TestClient, mocker: MagicMock):
    # Mock batches that match the expected response structure
    batches = [
        BatchSchemaDTO(
            reference="BATCH-001", sku="BLUE_CHAIR", eta=date(2024, 1, 15), qty=20
        ),
        BatchSchemaDTO(
            reference="BATCH-002", sku="RED_CHAIR", eta=date(2024, 1, 20), qty=15
        ),
    ]
    mock_get_batches = mocker.patch.object(
        BatchService, "get_batches", return_value=batches
    )

    res = client.get("/batch")

    assert res.status_code == status.HTTP_200_OK
    assert len(res.json()) == 2

    # Verify the response structure matches expected schema
    response_data = res.json()
    assert response_data[0]["reference"] == "BATCH-001"
    assert response_data[0]["sku"] == "BLUE_CHAIR"
    assert response_data[1]["reference"] == "BATCH-002"
    assert response_data[1]["sku"] == "RED_CHAIR"

    mock_get_batches.assert_called_once_with()


def test_get_batches_empty_list_returns_200(client: TestClient, mocker: MagicMock):
    mock_get_batches = mocker.patch.object(BatchService, "get_batches", return_value=[])

    res = client.get("/batch")

    assert res.status_code == status.HTTP_200_OK
    assert res.json() == []
    mock_get_batches.assert_called_once_with()


def test_get_batch_by_ref_happy_path_returns_200(client: TestClient, mocker: MagicMock):
    batch = BatchSchemaDTO(
        reference="BATCH-001", sku="BLUE_CHAIR", eta=date(2024, 1, 15), qty=20
    )
    mock_get_batch = mocker.patch.object(
        BatchService, "get_batche_by_ref", return_value=batch
    )

    res = client.get("/batch/BATCH-001")

    assert res.status_code == status.HTTP_200_OK

    # Verify response structure
    response_data = res.json()
    assert response_data["reference"] == "BATCH-001"
    assert response_data["sku"] == "BLUE_CHAIR"

    mock_get_batch.assert_called_once_with("BATCH-001")


def test_get_batch_by_ref_with_special_characters(
    client: TestClient, mocker: MagicMock
):
    batch_ref = "BATCH-001-SPECIAL"
    batch = BatchSchemaDTO(
        reference=batch_ref, sku="BLUE_CHAIR", eta=date(2024, 1, 15), qty=20
    )
    mock_get_batch = mocker.patch.object(
        BatchService, "get_batche_by_ref", return_value=batch
    )

    res = client.get(f"/batch/{batch_ref}")

    assert res.status_code == status.HTTP_200_OK
    mock_get_batch.assert_called_once_with(batch_ref)


def test_delete_batch_happy_path_returns_200(client: TestClient, mocker: MagicMock):
    mock_delete_batch = mocker.patch.object(BatchService, "delete_batch")

    res = client.delete("/batch/BATCH-001")

    assert res.status_code == status.HTTP_200_OK
    assert res.json() is None
    mock_delete_batch.assert_called_once_with("BATCH-001")


def test_delete_batch_with_special_characters(client: TestClient, mocker: MagicMock):
    batch_ref = "BATCH-001-SPECIAL"
    mock_delete_batch = mocker.patch.object(BatchService, "delete_batch")

    res = client.delete(f"/batch/{batch_ref}")

    assert res.status_code == status.HTTP_200_OK
    mock_delete_batch.assert_called_once_with(batch_ref)


def test_add_batch_validates_required_fields(client: TestClient):
    # Test missing required fields
    incomplete_data = {
        "ref": "BATCH-001",
        # Missing sku and qty
    }

    res = client.post("/batch", json=incomplete_data)

    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_detail = res.json()["detail"]

    # Should have validation errors for missing fields
    missing_fields = {error["loc"][-1] for error in error_detail}
    assert "sku" in missing_fields
    assert "qty" in missing_fields


def test_add_batch_validates_data_types(client: TestClient):
    # Test invalid data types
    invalid_data = {
        "ref": "BATCH-001",
        "sku": "BLUE_CHAIR",
        "qty": "not_a_number",  # Should be int
        "eta": "invalid_date",  # Should be valid date format
    }

    res = client.post("/batch", json=invalid_data)

    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# TODO: def test_add_batch_validates_positive_quantity(client: TestClient):
#     # Test negative quantity
#     invalid_data = {
#         "ref": "BATCH-001",
#         "sku": "BLUE_CHAIR",
#         "qty": -5,  # Should be positive
#         "eta": None
#     }
#
#     res = client.post("/batch", json=invalid_data)
#
#     assert res.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]


def test_endpoints_use_correct_content_type(client: TestClient, mocker: MagicMock):
    mock_add_batch = mocker.patch.object(BatchService, "add_batch")

    # Test that JSON content type works
    request_data = {"ref": "BATCH-001", "sku": "BLUE_CHAIR", "qty": 20, "eta": None}

    res = client.post("/batch", json=request_data)
    assert res.status_code == status.HTTP_201_CREATED


def test_batch_service_dependency_injection_works(
    client: TestClient, mocker: MagicMock
):
    """Test that the dependency injection is working correctly"""
    mock_get_batches = mocker.patch.object(BatchService, "get_batches", return_value=[])

    res = client.get("/batch")

    assert res.status_code == status.HTTP_200_OK
    mock_get_batches.assert_called_once_with()


# TODO: test_add_batch_duplicate_reference_returns_400
# TODO: test_get_batch_not_found_returns_404
# TODO: test_delete_batch_not_found_returns_404
# TODO: test_add_batch_invalid_sku_reference_returns_400
# TODO: test_batch_operations_with_authentication
# TODO: test_batch_operations_rate_limiting
