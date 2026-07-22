from fastapi.testclient import TestClient
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


def test_revenue_trend_endpoint(monkeypatch):
    mock_data = [{"date": "2023-01-01", "revenue": 1500.50}]
    monkeypatch.setattr("src.main.get_revenue_trend", lambda: mock_data)
    response = client.get("/api/revenue-trend")
    assert response.status_code == 200
    assert response.json() == mock_data


def test_top_products_endpoint(monkeypatch):
    mock_data = [{"name": "Product A", "total_revenue": 2500.0, "units_sold": 50}]
    monkeypatch.setattr("src.main.get_top_products", lambda limit=10: mock_data)
    response = client.get("/api/top-products?limit=5")
    assert response.status_code == 200
    assert response.json() == mock_data


def test_order_status_endpoint(monkeypatch):
    mock_data = [{"status": "Complete", "count": 120}]
    monkeypatch.setattr("src.main.get_order_status_breakdown", lambda: mock_data)
    response = client.get("/api/order-status")
    assert response.status_code == 200
    assert response.json() == mock_data


def test_category_performance_endpoint(monkeypatch):
    mock_data = [{"category": "Apparel", "total_revenue": 8000.0, "units_sold": 200}]
    monkeypatch.setattr("src.main.get_category_performance", lambda: mock_data)
    response = client.get("/api/category-performance")
    assert response.status_code == 200
    assert response.json() == mock_data
