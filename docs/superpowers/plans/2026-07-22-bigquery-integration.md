# BigQuery Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace CSV file reading in `src/data_service.py` with live queries against `bigquery-public-data.thelook_ecommerce` using `google-cloud-bigquery`.

**Architecture:** Use a single shared `google.cloud.bigquery.Client` in `src/data_service.py` with GCP Project ID resolved dynamically from environment variables (`GCP_PROJECT` / `GOOGLE_CLOUD_PROJECT`), falling back to `bigquery-public-data`. Execute parameterized SQL queries for dashboard panels.

**Tech Stack:** Python 3.11, FastAPI, `google-cloud-bigquery>=3.0.0`, `pytest`, `pytest-mock`.

## Global Constraints
- `google-cloud-bigquery>=3.0.0` dependency added to `pyproject.toml`.
- Dashboard API responses must retain exact dictionary field names and data types.
- Target dataset: `bigquery-public-data.thelook_ecommerce`.
- BigQuery SQL queries must be optimized with aggregations.

---

### Task 1: Add BigQuery Dependency & Client Setup

**Files:**
- Modify: `pyproject.toml:6-10`
- Modify: `src/data_service.py:1-100`
- Create: `tests/test_data_service.py`

**Interfaces:**
- Consumes: Environment variables `GCP_PROJECT`, `GOOGLE_CLOUD_PROJECT`.
- Produces: `get_bigquery_client() -> bigquery.Client` helper and dataset configuration.

- [ ] **Step 1: Write tests for client initialization & project ID resolution**

```python
import os
import pytest
from unittest.mock import MagicMock, patch
from src.data_service import get_bigquery_client

def test_get_bigquery_client_default(monkeypatch):
    monkeypatch.delenv("GCP_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    with patch("google.cloud.bigquery.Client") as mock_client:
        client = get_bigquery_client()
        mock_client.assert_called_once_with(project="bigquery-public-data")

def test_get_bigquery_client_env_override(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT", "my-custom-gcp-project")
    with patch("google.cloud.bigquery.Client") as mock_client:
        client = get_bigquery_client()
        mock_client.assert_called_once_with(project="my-custom-gcp-project")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_data_service.py`
Expected: FAIL with `ModuleNotFoundError` or `ImportError: cannot import name 'get_bigquery_client'`

- [ ] **Step 3: Update `pyproject.toml` and implement `get_bigquery_client()` in `src/data_service.py`**

In `pyproject.toml`:
```toml
dependencies = [
    "fastapi[standard]>=0.115.0",
    "pandas>=2.2.0",
    "jinja2>=3.1.0",
    "google-cloud-bigquery>=3.0.0",
]
```

In `src/data_service.py`:
```python
import os
from google.cloud import bigquery

DATASET_ID = "bigquery-public-data.thelook_ecommerce"

_client = None

def get_bigquery_client() -> bigquery.Client:
    global _client
    if _client is None:
        project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "bigquery-public-data"
        _client = bigquery.Client(project=project_id)
    return _client
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_data_service.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/data_service.py tests/test_data_service.py
git commit -m "feat: add google-cloud-bigquery dependency and client initializer"
```

---

### Task 2: Implement BigQuery SQL Queries in `data_service.py`

**Files:**
- Modify: `src/data_service.py`
- Modify: `tests/test_data_service.py`

**Interfaces:**
- Consumes: `get_bigquery_client()`, `bigquery-public-data.thelook_ecommerce` tables (`orders`, `order_items`, `products`).
- Produces: Updated functions `get_revenue_trend()`, `get_top_products()`, `get_order_status_breakdown()`, `get_category_performance()`, `get_dashboard_summary()`.

- [ ] **Step 1: Write unit tests with mocked BigQuery query execution**

```python
import datetime
from unittest.mock import MagicMock, patch
from src.data_service import (
    get_revenue_trend,
    get_top_products,
    get_order_status_breakdown,
    get_category_performance,
    get_dashboard_summary,
)

def test_get_revenue_trend(monkeypatch):
    mock_client = MagicMock()
    mock_row = {"date": datetime.date(2023, 1, 1), "revenue": 1500.50}
    mock_client.query.return_value.result.return_value = [mock_row]
    monkeypatch.setattr("src.data_service.get_bigquery_client", lambda: mock_client)

    result = get_revenue_trend()
    assert result == [{"date": "2023-01-01", "revenue": 1500.50}]

def test_get_dashboard_summary(monkeypatch):
    mock_client = MagicMock()
    mock_row = {"total_orders": 100, "total_revenue": 5000.0}
    mock_client.query.return_value.result.return_value = [mock_row]
    monkeypatch.setattr("src.data_service.get_bigquery_client", lambda: mock_client)

    result = get_dashboard_summary()
    assert result == {
        "total_orders": 100,
        "total_revenue": 5000.0,
        "avg_order_value": 50.0,
        "data_source": "BigQuery",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_data_service.py`
Expected: FAIL because functions still query CSV files.

- [ ] **Step 3: Replace CSV reading with BigQuery SQL in `src/data_service.py`**

```python
import os
from google.cloud import bigquery

DATASET_ID = "bigquery-public-data.thelook_ecommerce"
_client = None


def get_bigquery_client() -> bigquery.Client:
    global _client
    if _client is None:
        project_id = (
            os.getenv("GCP_PROJECT")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or "bigquery-public-data"
        )
        _client = bigquery.Client(project=project_id)
    return _client


def get_revenue_trend() -> list[dict]:
    client = get_bigquery_client()
    query = f"""
        SELECT
            DATE(oi.created_at) AS date,
            ROUND(SUM(oi.sale_price), 2) AS revenue
        FROM `{DATASET_ID}.order_items` oi
        JOIN `{DATASET_ID}.orders` o ON oi.order_id = o.order_id
        WHERE o.status = 'Complete'
        GROUP BY date
        ORDER BY date ASC
    """
    rows = client.query(query).result()
    return [
        {"date": str(row["date"]), "revenue": float(row["revenue"])}
        for row in rows
    ]


def get_top_products(limit: int = 10) -> list[dict]:
    client = get_bigquery_client()
    query = f"""
        SELECT
            p.name,
            ROUND(SUM(oi.sale_price), 2) AS total_revenue,
            COUNT(*) AS units_sold
        FROM `{DATASET_ID}.order_items` oi
        JOIN `{DATASET_ID}.products` p ON oi.product_id = p.id
        GROUP BY p.id, p.name
        ORDER BY total_revenue DESC
        LIMIT @limit
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("limit", "INT64", limit)]
    )
    rows = client.query(query, job_config=job_config).result()
    return [
        {
            "name": row["name"],
            "total_revenue": float(row["total_revenue"]),
            "units_sold": int(row["units_sold"]),
        }
        for row in rows
    ]


def get_order_status_breakdown() -> list[dict]:
    client = get_bigquery_client()
    query = f"""
        SELECT
            status,
            COUNT(*) AS count
        FROM `{DATASET_ID}.orders`
        GROUP BY status
    """
    rows = client.query(query).result()
    return [
        {"status": row["status"], "count": int(row["count"])}
        for row in rows
    ]


def get_category_performance() -> list[dict]:
    client = get_bigquery_client()
    query = f"""
        SELECT
            p.category,
            ROUND(SUM(oi.sale_price), 2) AS total_revenue,
            COUNT(*) AS units_sold
        FROM `{DATASET_ID}.order_items` oi
        JOIN `{DATASET_ID}.products` p ON oi.product_id = p.id
        GROUP BY p.category
        ORDER BY total_revenue DESC
    """
    rows = client.query(query).result()
    return [
        {
            "category": row["category"],
            "total_revenue": float(row["total_revenue"]),
            "units_sold": int(row["units_sold"]),
        }
        for row in rows
    ]


def get_dashboard_summary() -> dict:
    client = get_bigquery_client()
    query = f"""
        SELECT
            (SELECT COUNT(*) FROM `{DATASET_ID}.orders`) AS total_orders,
            (SELECT ROUND(SUM(sale_price), 2) FROM `{DATASET_ID}.order_items`) AS total_revenue
    """
    rows = list(client.query(query).result())
    if not rows:
        return {"total_orders": 0, "total_revenue": 0.0, "avg_order_value": 0.0, "data_source": "BigQuery"}
    
    row = rows[0]
    total_orders = int(row["total_orders"] or 0)
    total_revenue = float(row["total_revenue"] or 0.0)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "data_source": "BigQuery",
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_data_service.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/data_service.py tests/test_data_service.py
git commit -m "feat: replace CSV data functions with BigQuery live SQL queries"
```

---

### Task 3: Integration Testing & Verification

**Files:**
- Create: `tests/test_api_routes.py`

**Interfaces:**
- Consumes: FastAPI endpoints in `src/main.py`.
- Produces: API integration verification.

- [ ] **Step 1: Write integration tests for API endpoints**

```python
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.main import app

client = TestClient(app)

def test_summary_endpoint(monkeypatch):
    mock_summary = {
        "total_orders": 124633,
        "total_revenue": 10500123.45,
        "avg_order_value": 84.25,
        "data_source": "BigQuery",
    }
    monkeypatch.setattr("src.main.get_dashboard_summary", lambda: mock_summary)
    response = client.get("/api/summary")
    assert response.status_code == 200
    assert response.json()["data_source"] == "BigQuery"

def test_dashboard_route_renders_bigquery(monkeypatch):
    mock_summary = {
        "total_orders": 124633,
        "total_revenue": 10500123.45,
        "avg_order_value": 84.25,
        "data_source": "BigQuery",
    }
    monkeypatch.setattr("src.main.get_dashboard_summary", lambda: mock_summary)
    response = client.get("/")
    assert response.status_code == 200
    assert "BigQuery" in response.text
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest tests/test_api_routes.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_api_routes.py
git commit -m "test: add integration test suite for FastAPI dashboard routes"
```
