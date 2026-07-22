import datetime
import os
import pytest
from unittest.mock import MagicMock, patch
import src.data_service
from src.data_service import (
    get_bigquery_client,
    get_revenue_trend,
    get_top_products,
    get_order_status_breakdown,
    get_category_performance,
    get_dashboard_summary,
)

@pytest.fixture(autouse=True)
def reset_client_singleton():
    src.data_service._client = None
    yield
    src.data_service._client = None

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

def test_get_revenue_trend(monkeypatch):
    mock_client = MagicMock()
    mock_row = {"date": datetime.date(2023, 1, 1), "revenue": 1500.50}
    mock_client.query.return_value.result.return_value = [mock_row]
    monkeypatch.setattr("src.data_service.get_bigquery_client", lambda: mock_client)

    result = get_revenue_trend()
    assert result == [{"date": "2023-01-01", "revenue": 1500.50}]

def test_get_top_products(monkeypatch):
    mock_client = MagicMock()
    mock_row = {"name": "Product A", "total_revenue": 2500.0, "units_sold": 50}
    mock_client.query.return_value.result.return_value = [mock_row]
    monkeypatch.setattr("src.data_service.get_bigquery_client", lambda: mock_client)

    result = get_top_products(limit=5)
    assert result == [{"name": "Product A", "total_revenue": 2500.0, "units_sold": 50}]

def test_get_order_status_breakdown(monkeypatch):
    mock_client = MagicMock()
    mock_row = {"status": "Complete", "count": 120}
    mock_client.query.return_value.result.return_value = [mock_row]
    monkeypatch.setattr("src.data_service.get_bigquery_client", lambda: mock_client)

    result = get_order_status_breakdown()
    assert result == [{"status": "Complete", "count": 120}]

def test_get_category_performance(monkeypatch):
    mock_client = MagicMock()
    mock_row = {"category": "Apparel", "total_revenue": 8000.0, "units_sold": 200}
    mock_client.query.return_value.result.return_value = [mock_row]
    monkeypatch.setattr("src.data_service.get_bigquery_client", lambda: mock_client)

    result = get_category_performance()
    assert result == [{"category": "Apparel", "total_revenue": 8000.0, "units_sold": 200}]

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
