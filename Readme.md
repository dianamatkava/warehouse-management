# Allocation Service Architecture

Below is an overview of the Allocation Service’s architecture, showing how each component fits together. This document is organized into logical sections that mirror the folder structure and the high-level diagram.

---

## Table of Contents

1. [Project Requirement](#project-requirement)
2. [High-Level Architecture](#high-level-architecture)
2. [Folder Structure](#folder-structure)
3. [Layered Breakdown](#layered-breakdown)
   * [1. Domain Layer](#1-domain-layer)
   * [2. Adapters & Persistence Layer](#2-adapters--persistence-layer)
   * [3. Services Layer](#3-services-layer)
   * [4. API / Routes Layer](#4-api--routes-layer)
   * [5. Shared Utilities & Configuration](#5-shared-utilities--configuration)
   * [6. Tests](#6-tests)
4. [Error Flow & Exception Handling](#error-flow--exception-handling)
5. [How It All Works Together](#how-it-all-works-together)
6. [Getting Started & Usage](#getting-started--usage)

---
## Project Requirement
This project is a warehouse management tool that separates customer orders from warehouse inventory through an “Allocation” bounded context:

1. **Order Capture**
   - Front-end/check-out service turns a cart into an `Order` with one or more `OrderLine(s)` (SKU + quantity).

2. **Warehouse Inventory**
   - Warehouse tracks `Batch` entities (unique reference, SKU, quantity, optional ETA).
   - Batches may be in-stock or inbound (with future ETA).

3. **Allocation Rules**
   - Match each `OrderLine` to one or more `Batch`es.
   - Never allocate more units than a batch’s available quantity.
   - Prevent double-allocation of the same line.
   - Prefer in-stock batches over inbound; among inbounds, choose the earliest ETA.

4. **Fulfillment Handoff**
   - After allocation, the Warehouse Management System generates pick-lists and reserves stock by batch reference.

---

## High-Level Architecture

Below is a detailed description of how the Allocation Service is structured, following a Clean (Onion) Architecture approach. The goal is to keep business rules (Domain) at the core, and to layer outward for persistence, application logic (Services), and the transport/API layer. We also adhere to Domain‐Driven Design (DDD), the Repository & Unit of Work patterns, and Dependency Injection (DI) for maximum separation of concerns and testability.

![Application Infrastructure Diagram](./assets/img.png)


* **Client → API**: HTTP requests hit FastAPI endpoints.
* **API → Services**: Incoming router models (DTOs) are converted, then service methods are invoked.
* **Services → UoW**: Service code calls the Unit of Work, which in turn uses repositories to perform CRUD on domain models.
* **UoW → ORM → Domain → DB**: The repository layer maps domain objects to database tables via SQLModel/SQLAlchemy.
* **Errors** can bubble up from Domain, ORM, or UoW; the API layer catches them and returns appropriate HTTP responses.

---

## Folder Structure

```
src/
├── allocations/
│   ├── adapters/
│   │   ├── __deprecated/        ← old/deprecated adapters
│   │   ├── orm.py               ← SQLModel/SQLAlchemy table definitions
│   │   ├── repository.py        ← Concrete repository implementations
│   │   └── uow.py               ← Unit of Work (session + repositories)
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   └── batch_domain_model.py ← Domain model definitions (Batch, Allocation)
│   │
│   ├── routes/
│   │   ├── exceptions/
│   │   │   ├── __init__.py
│   │   │   └── api_exceptions.py  ← FastAPI exception handlers & custom HTTP errors
│   │   │
│   │   ├── schemas/
│   │   │   ├── allocations/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── request_models.py   ← Pydantic models for incoming JSON
│   │   │   │   └── response_models.py  ← Pydantic models for outgoing JSON
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   ├── allocations.py          ← Aggregated import of allocation-related schemas
│   │   │   └── batches.py              ← Aggregated import of batch-related schemas
│   │   │
│   │   ├── __init__.py
│   │   ├── allocations.py             ← APIRouter for /allocations endpoints
│   │   └── batches.py                 ← APIRouter for /batch endpoints
│   │
│   ├── services/
│   │   ├── transformers/
│   │   │   ├── __init__.py
│   │   │   └── batch_transformers.py   ← Helper functions to convert domain ↔ DTO
│   │   │
│   │   ├── __init__.py
│   │   ├── batch_service.py            ← Business logic for creating, listing, allocating, deallocating
│   │   ├── exceptions.py               ← Service-level error definitions (ServiceError, etc.)
│   │   └── schemas.py                  ← Service-level DTOs / Pydantic models (BatchSchemaDTO, AllocationSchemaDTO)
│   │
│   ├── tests/
│   │   ├── e2e/
│   │   │   ├── __init__.py
│   │   │   ├── confest.py
│   │   │   └── test_api.py             ← End-to-end tests against FastAPI
│   │   │
│   │   ├── integration/
│   │   │   ├── __init__.py
│   │   │   ├── test_orm.py             ← Integration tests for ORM mappings
│   │   │   └── test_repository.py      ← Integration tests for repository + database
│   │   │
│   │   └── unit/
│   │       ├── __init__.py
│   │       ├── test_batch_service.py   ← Unit tests for service methods
│   │       ├── test_domain.py          ← Unit tests for domain model invariants
│   │       └── confest.py              ← Pytest fixtures for unit tests
│   │
│   └── __init__.py
│
├── shared/
│   └── utils/
│       └── __init__.py                ← Reusable utilities (logging, helpers, etc.)
│
├── units/
│   └── __init__.py                    ← (Optional: global or legacy code/tests)
│
├── app.py                             ← FastAPI application factory / router includes
├── settings.py                        ← App configuration (env loading, DB URL, etc.)
├── setup.py                           ← Package metadata (name="allocation", packages=["allocation"])
├── .env.test                          ← Test environment variables
└── .env                               ← Local environment variables
```

---

## Layered Breakdown

### 1. Domain Layer

* **Location:** `src/allocations/domain/batch_domain_model.py`
* **Responsibility:**

  * Defines core business entities (`Batch`, `Allocation`, possibly `OrderLine`).
  * Enforces invariants (e.g., a batch cannot allocate more than its available quantity).
  * Does *not* know anything about HTTP or databases—pure Python classes (or SQLModel models that include Python business logic).

```python
# Example (simplified) from product_model.py

from typing import List, Optional
from datetime import date

class Allocation:
    def __init__(self, order_id: str, sku: str, qty: int):
        self.order_id = order_id
        self.sku = sku
        self.qty = qty

class Batch:
    def __init__(self, reference: str, sku: str, purchased_qty: int, eta: Optional[date]):
        self.reference = reference
        self.sku = sku
        self.purchased_quantity = purchased_qty
        self.eta = eta
        self._allocations: List[Allocation] = []

    @property
    def allocated_quantity(self) -> int:
        return sum(a.qty for a in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self.purchased_quantity - self.allocated_quantity

    def allocate(self, order_id: str, qty: int) -> None:
        if qty <= self.available_quantity:
            self._allocations.append(Allocation(order_id, self.sku, qty))
        else:
            raise AllocationError(f"Not enough stock in batch {self.reference}")

    def deallocate(self, order_id: str) -> None:
        self._allocations = [a for a in self._allocations if a.order_id != order_id]
```

---

### 2. Adapters & Persistence Layer

> **Purpose:** Provide an abstraction between domain logic and the actual database. We use a Unit of Work and repository pattern to keep transaction management and data‐access concerns separate.

* **Location:** `src/allocations/adapters/`

  * `orm.py`

    * Defines ORM/SQLModel table classes (e.g., `BatchORM`, `AllocationORM`) that mirror the domain model.
    * Handles mapping between SQL rows and in‐memory objects (often using `.from_orm(...)`, `.to_orm()`, or similar).
  * `repository.py`

    * Implements concrete repository classes (e.g., `BatchRepository`) that fulfill an abstract interface (e.g., `AbstractBatchRepo`).
    * Contains methods like `add(batch: Batch)`, `get_by_ref(ref: str) -> Batch`, `list_all() -> List[Batch]`, `find_available(sku, qty) -> Optional[Batch]`, etc.
    * Wraps ORM calls in simple Python methods.
  * `uow.py`

    * Defines a `UnitOfWork` class (e.g., `SqlAlchemyUnitOfWork`) that:

      1. Creates a database session/connection.
      2. Instantiates repository objects for that session (e.g., `self.batches = BatchRepository(session)`).
      3. Provides `commit()` and `rollback()` methods.
      4. Ensures all database operations in a single business transaction are atomic.

```python
# Example sketch from adapters/uow.py

from sqlalchemy.orm import Session
from .repository import BatchRepository
from .orm import SessionLocal  # SQLModel session factory

class UnitOfWork:
    def __enter__(self):
        self.session: Session = SessionLocal()
        self.batches = BatchRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
```

---

### 3. Services Layer

> **Purpose:** Encapsulate application/business logic. Services coordinate domain operations and repository/UoW usage, and expose simple methods for CRUD and allocation/deallocation flows.

* **Location:** `src/allocations/services/`

  * `batch_service.py`

    * Contains a `BatchService` class with methods such as:

      * `create_batch(dto: BatchSchemaDTO) -> BatchSchemaDTO`
      * `list_batches() -> List[BatchSchemaDTO]`
      * `get_batch(ref: str) -> BatchSchemaDTO`
      * `delete_batch(ref: str)`
      * `allocate_order(order_line: OrderLineModel) -> AllocationSchemaDTO`
      * `deallocate_order(order_id: str, batch_ref: str)`
    * Internally, each method:

      1. Opens a `UnitOfWork` (`with UnitOfWork() as uow:`).
      2. Uses `uow.batches` repository to query or update domain objects.
      3. Converts **domain models** to **service‐level DTOs** (`schemas.py`) via transformer helpers.
    * Raises service‐level exceptions (`ServiceError` in `exceptions.py`) if business rules fail (e.g., no batch available to allocate).
  * `exceptions.py`

    * Defines custom service errors (e.g., `BatchNotFound`, `OutOfStockError`, `ServiceError`) that are caught by the API layer and translated into proper HTTP responses.
  * `schemas.py`

    * Contains Pydantic models used within the service layer (e.g., `BatchSchemaDTO`, `AllocationSchemaDTO`). These mirror domain attributes plus any computed fields (available/allocated quantities).
  * `transformers/batch_transformers.py`

    * Helper functions that convert between domain objects (`Batch`, `Allocation`) and DTOs (`BatchSchemaDTO`, `AllocationSchemaDTO`).

```python
# Example from services/test_product_service.py

from typing import List
from ..adapters.uow import UnitOfWork
from .schemas import BatchSchemaDTO, AllocationSchemaDTO
from .exceptions import BatchNotFound, OutOfStockError
from .transformers.batch_transformers import domain_batch_to_schema

class BatchService:
    def list_batches(self) -> List[BatchSchemaDTO]:
        with UnitOfWork() as uow:
            domain_batches = uow.batches.list_all()
            return [domain_batch_to_schema(b) for b in domain_batches]

    def create_batch(self, dto: BatchSchemaDTO) -> BatchSchemaDTO:
        from ..domain.batch_domain_model import Batch
        new_batch = Batch(
            reference=dto.reference,
            sku=dto.sku,
            purchased_quantity=dto.purchased_quantity,
            eta=dto.eta,
        )
        with UnitOfWork() as uow:
            uow.batches.add(new_batch)
        return domain_batch_to_schema(new_batch)

    def allocate_order(self, order_line_model) -> AllocationSchemaDTO:
        from ..domain.batch_domain_model import OrderLine
        line = OrderLine(**order_line_model.dict())
        with UnitOfWork() as uow:
            batch = uow.batches.find_available(line.sku, line.qty)
            if not batch:
                raise OutOfStockError(f"No batch found for SKU {line.sku}")
            batch.allocate(line.order_id, line.qty)   # domain logic
            uow.batches.update(batch)
            return AllocationSchemaDTO.from_batch_and_order(batch, line)
```

---

### 4. API / Routes Layer

> **Purpose:** Expose HTTP endpoints using FastAPI, validate incoming JSON via Pydantic, call service methods, and transform service outputs into HTTP responses.

* **Location:** `src/allocations/routes/`

  * `allocations.py`

    * Defines an `APIRouter(prefix="/allocations", tags=["Allocations"])` with endpoints such as:

      * `GET  /allocations` → `get_allocations()`
      * `POST /allocations` → `allocate_order()`
      * `DELETE /allocations/{order_id}/batch/{ref}` → `deallocate_order()`
    * Each endpoint:

      1. Accepts a Pydantic **request model** from `schemas/allocations/request_models.py` (e.g. `AllocationRequestModel`).
      2. Calls a corresponding service method (via dependency injection).
      3. Returns a response Pydantic **response model** (from `schemas/allocations/response_models.py`), or raises an HTTPException if the service raised a `ServiceError`.
  * `batches.py`

    * Defines a separate `APIRouter(prefix="/batch", tags=["Batches"])` with endpoints such as:

      * `GET  /batch` → `list_batches()`
      * `POST /batch` → `create_batch()`
      * `GET  /batch/{ref}` → `get_batch(ref)`
      * `DELETE /batch/{ref}` → `delete_batch(ref)`
    * Uses request models from `schemas/batches` and response models from the same.
  * `exceptions/api_exceptions.py`

    * Contains a FastAPI exception handler that catches service‐level exceptions and maps them to `HTTPException(status_code, detail)`. For example:

      ```python
      from fastapi import Request, HTTPException
      from fastapi.responses import JSONResponse
      from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
      from ..services.exceptions import BatchNotFound, OutOfStockError

      @app.exception_handler(BatchNotFound)
      async def batch_not_found_handler(request: Request, exc: BatchNotFound):
          return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"detail": str(exc)})

      @app.exception_handler(OutOfStockError)
      async def out_of_stock_handler(request: Request, exc: OutOfStockError):
          return JSONResponse(status_code=HTTP_409_CONFLICT, content={"detail": str(exc)})
      ```
    * Ensures the client always receives a well‐formed JSON error with the correct HTTP status code.

```python
# Example from routes/batches.py

from fastapi import APIRouter, Depends, HTTPException, status
from ..services.batch_service import BatchService
from ..routes.schemas.batches import (
    BatchesCreationModelRequestModel,
    BatchResponseModel,
    BatchesListResponseModel,
)
from ..routes.exceptions.api_exceptions import BatchNotFound

router = APIRouter(prefix="/batch", tags=["Batches"])

@router.get("", response_model=BatchesListResponseModel)
def list_batches(service: BatchService = Depends()):
    batch_dtos = service.list_batches()
    return BatchesListResponseModel(__root__=batch_dtos)

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BatchResponseModel,
)
def create_batch(
    payload: BatchesCreationModelRequestModel,
    service: BatchService = Depends(),
):
    dto = payload.to_service_dto()
    batch_schema = service.create_batch(dto)
    return BatchResponseModel.from_service_schema(batch_schema)

@router.get("/{ref}", response_model=BatchResponseModel)
def get_batch(ref: str, service: BatchService = Depends()):
    try:
        batch_schema = service.get_batch(ref)
        return BatchResponseModel.from_service_schema(batch_schema)
    except BatchNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.delete("/{ref}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch(ref: str, service: BatchService = Depends()):
    try:
        service.delete_batch(ref)
    except BatchNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return None
```

---

### 5. Shared Utilities & Configuration

* **Location:**

  * `src/shared/utils/` ← Reusable helper functions or modules (e.g., logging setup, string utilities, pagination helpers).

  * `src/settings.py` ← Application configuration (e.g., loading environment variables, building the `DATABASE_URL`, or setting feature flags).

  * `src/app.py` ← FastAPI application factory. This is where you import routers and exception handlers and create the `app = FastAPI()` instance:

    ```python
    from fastapi import FastAPI
    from allocations.routes.batches import router as batch_router
    from allocations.routes.allocations import router as alloc_router
    from allocations.routes.exceptions.api_exceptions import (
        batch_not_found_handler,
        out_of_stock_handler,
    )
    from settings import get_settings

    def create_app():
        app = FastAPI(title="Allocation Service")
        app.include_router(batch_router)
        app.include_router(alloc_router)

        # Register custom exception handlers
        app.add_exception_handler(BatchNotFound, batch_not_found_handler)
        app.add_exception_handler(OutOfStockError, out_of_stock_handler)

        return app

    app = create_app()
    ```

  * `src/setup.py` ← Package metadata. For local development, this allows you to `pip install -e src/` or build a distributable. It lists `packages=["allocation"]`, meaning the `allocations` package will be installed under that name.

---

### 6. Tests

> **Purpose:** Validate each layer in isolation (unit), verify integration of components (integration), and run end-to-end (E2E) checks against the live HTTP API.

* **Location:** `src/allocations/tests/`

  * **Unit Tests (`unit/`)**

    * `test_batch_service.py` ← Covers pure service logic (e.g., “Given a fresh batch, allocating more than available should raise OutOfStockError”).
    * `test_domain.py` ← Validates domain model invariants (e.g., `available_quantity`, “allocations reduce quantity,” “deallocate frees up space”).
    * `conftest.py` ← Pytest fixtures for mocking repositories or domain objects.
  * **Integration Tests (`integration/`)**

    * `test_orm.py` ← Verifies ORM mappings (e.g., creating a `BatchORM` row and reading back a `Batch` domain object correctly).
    * `test_repository.py` ← Tests real database interactions (e.g., “When I add a batch via the repository and commit, I can query it by reference”).
    * `test_routers.py` ← “Database + FastAPI” integration: spin up a test database, run the FastAPI server in a test client, and ensure HTTP endpoints behave correctly (404 when missing, 201 on create, etc.).
    * `confest.py` ← Fixtures for setting up a test database, a test client, and transactional cleanup.
  * **End-to-End Tests (`e2e/`)**

    * `test_api.py` ← Tests HTTP responses against a fully running server (either with a real database container or SQLite in-memory).
    * `confest.py` ← Similar to integration fixtures, but focused on launching the “entire app.”

---

## Error Flow & Exception Handling

1. **Domain Errors (`ModelError`)**

   * Errors raised inside `batch_domain_model.py` (e.g. `AllocationError`) are caught by the service.
   * The service may wrap them or re-raise them as `ServiceError`/`BatchNotFound`/`OutOfStockError` (as appropriate).

2. **Database/ORM Errors (`DBError`)**

   * If the ORM or repository layer encounters an integrity error (e.g., unique constraint on `batch.reference`), it raises a `DBError` (custom exception).
   * The service layer can catch or let it bubble up as a generic `ServiceError`.

3. **Service Errors (`ServiceError`, `BatchNotFound`, `OutOfStockError`)**

   * Defined in `src/allocations/services/exceptions.py`.
   * The API layer’s exception handlers (in `api_exceptions.py`) map these to proper HTTP codes:

     * `BatchNotFound` → `HTTP 404 Not Found`
     * `OutOfStockError` → `HTTP 409 Conflict`
     * Generic `ServiceError` → `HTTP 400 Bad Request` (or another default)

4. **API Layer**

   * Catches `ServiceError` (and its subclasses) and returns a JSON response with the appropriate `status_code` and `{"detail": "<message>"}`.
   * Any unhandled exception becomes a `500 Internal Server Error`.

---

## How It All Works Together

1. **Startup**

   * `uvicorn src.app:app` spins up the FastAPI application (`app = create_app()`).
   * All routers (`batches`, `allocations`) and exception handlers are registered.

2. **Client Request**

   * A client (cURL, browser, or another service) sends `POST /batch` with JSON payload.
   * FastAPI validates that payload against `BatchesCreationModelRequestModel`.

3. **Routing to Service**

   * The validated Pydantic model is handed to the `create_batch` endpoint in `routes/batches.py`.
   * That endpoint constructs a service DTO (e.g., `BatchCreateDTO`) and calls `BatchService.create_batch(dto)`.

4. **Business Logic & Persistence**

   * Inside `BatchService.create_batch()`, a new `Batch` domain object is created and passed to the repository inside a `UnitOfWork`.
   * The repository maps the domain `Batch` to `BatchORM` (SQLModel) and persists it to the database.
   * Once committed, the domain object is returned (or a fresh query happens), and then converted into a `BatchSchemaDTO` (service DTO).

5. **API Response**

   * The endpoint receives `BatchSchemaDTO` from the service, converts it into `BatchResponseModel`, and returns it as JSON with `HTTP 201 Created`.
   * The client receives `{ "reference": "...", "sku": "...", "available_quantity": ..., ... }`.

6. **Error Scenario (Allocation)**

   * Client calls `POST /allocations` with `{ "order_id": "O1", "sku": "FOO", "qty": 10 }`.
   * FastAPI validates the payload against `AllocationRequestModel`.
   * The endpoint calls `BatchService.allocate_order(...)`.
   * Service attempts `uow.batches.find_available("FOO", 10)`, but no batch has enough stock. It raises `OutOfStockError`.
   * The API’s exception handler for `OutOfStockError` catches it and returns `HTTP 409 Conflict` with `{"detail": "No batch found for SKU FOO"}`.

---

## Getting Started & Usage

1. **Install dependencies**

   ```bash
   poetry install
   ```

2. **Set up the database**
   * Configure your `DATABASE_URL` in `.env` and `alembic.ini` (e.g. `postgresql://user:pass@localhost:5432/allocation_db`).
   * Run migrations using Alembic:

     ```shell
     # Create migration
     alembic revision --autogenerate -m "your message"
     # Apply migration
     alembic upgrade head
     ```

3. **Run the server**

   ```bash
   uvicorn src.app:app --reload
   ```

   * By default, FastAPI serves docs at:

     * **Swagger UI**: `http://127.0.0.1:8000/docs`
     * **ReDoc**: `http://127.0.0.1:8000/redoc`

4. **Run tests**

   ```bash
   # Unit + Integration
   pytest src/allocations/tests/unit
   pytest src/allocations/tests/integration

   # End-to-End
   pytest src/allocations/tests/e2e
   ```

---

### Summary

* **Domain Layer** holds the core business rules (`Batch`, `Allocation`).
* **Adapters & Persistence** (Repository + Unit of Work) manage database sessions and translate domain ↔ ORM.
* **Services** implement use cases (CRUD + allocate/deallocate) purely in terms of domain objects and DTOs.
* **API / Routes** expose HTTP endpoints, validate request payloads, call services, and format responses.
* **Errors** bubble up from domain/DB into service, then get caught and converted into HTTP error codes by the API.
* **Tests** are organized into unit, integration, and E2E, ensuring each layer is verified both in isolation and end-to-end.

This layered, feature-first structure keeps each concern clearly separated, makes individual components easy to test, and ensures that business logic remains decoupled from web or database frameworks.



### Linting / Formating / Strict Type Annotation

Fix missing `stub` by running:

```shell
mypy --install-types
```


```shell
psql -U postgresql # login to pg
\l # list databases
```
