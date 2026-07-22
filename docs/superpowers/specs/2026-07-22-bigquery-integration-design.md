# BigQuery Integration Design Specification

## Overview
This specification details replacing the existing CSV file-based data ingestion in the E-commerce Analytics Dashboard with live queries against Google BigQuery dataset `bigquery-public-data.thelook_ecommerce` using the `google-cloud-bigquery` Python client library.

## Goals
- Replace static CSV data parsing (`orders.csv`, `order_items.csv`, `products.csv`) in `src/data_service.py` with direct SQL queries to BigQuery.
- Query full live dataset (`bigquery-public-data.thelook_ecommerce`) instead of sample 500-row CSV files.
- Preserve existing API contracts and dashboard panel functionality:
  - Revenue trend (`/api/revenue-trend`)
  - Top products (`/api/top-products`)
  - Order status breakdown (`/api/order-status`)
  - Category performance (`/api/category-performance`)
  - Summary metadata (`/api/summary` & `/` template context)
- Update data source indicator in summary to `"BigQuery"`.

## Architecture & Configuration

### Dependencies
Update `pyproject.toml` to include:
- `google-cloud-bigquery>=3.0.0`

### Client Initialization & Project Resolution
- BigQuery client initialized lazily or once as a module-level singleton in `src/data_service.py`.
- GCP Project ID resolution order:
  1. `GCP_PROJECT` environment variable
  2. `GOOGLE_CLOUD_PROJECT` environment variable
  3. Default fallback: `"bigquery-public-data"`

Target Dataset: `bigquery-public-data.thelook_ecommerce`

## Query Specifications

### 1. Revenue Trend (`get_revenue_trend`)
- **SQL Query**:
  ```sql
  SELECT
    DATE(oi.created_at) AS date,
    ROUND(SUM(oi.sale_price), 2) AS revenue
  FROM `bigquery-public-data.thelook_ecommerce.order_items` oi
  JOIN `bigquery-public-data.thelook_ecommerce.orders` o
    ON oi.order_id = o.order_id
  WHERE o.status = 'Complete'
  GROUP BY date
  ORDER BY date ASC
  ```
- **Output Format**: `list[dict]` containing `{"date": "YYYY-MM-DD", "revenue": float}`.

### 2. Top Products (`get_top_products(limit: int = 10)`)
- **SQL Query**:
  ```sql
  SELECT
    p.name,
    ROUND(SUM(oi.sale_price), 2) AS total_revenue,
    COUNT(*) AS units_sold
  FROM `bigquery-public-data.thelook_ecommerce.order_items` oi
  JOIN `bigquery-public-data.thelook_ecommerce.products` p
    ON oi.product_id = p.id
  GROUP BY p.id, p.name
  ORDER BY total_revenue DESC
  LIMIT @limit
  ```
- **Parameters**: `ScalarQueryParameter("limit", "INT64", limit)`.
- **Output Format**: `list[dict]` containing `{"name": str, "total_revenue": float, "units_sold": int}`.

### 3. Order Status Breakdown (`get_order_status_breakdown`)
- **SQL Query**:
  ```sql
  SELECT
    status,
    COUNT(*) AS count
  FROM `bigquery-public-data.thelook_ecommerce.orders`
  GROUP BY status
  ```
- **Output Format**: `list[dict]` containing `{"status": str, "count": int}`.

### 4. Category Performance (`get_category_performance`)
- **SQL Query**:
  ```sql
  SELECT
    p.category,
    ROUND(SUM(oi.sale_price), 2) AS total_revenue,
    COUNT(*) AS units_sold
  FROM `bigquery-public-data.thelook_ecommerce.order_items` oi
  JOIN `bigquery-public-data.thelook_ecommerce.products` p
    ON oi.product_id = p.id
  GROUP BY p.category
  ORDER BY total_revenue DESC
  ```
- **Output Format**: `list[dict]` containing `{"category": str, "total_revenue": float, "units_sold": int}`.

### 5. Summary Metadata (`get_dashboard_summary`)
- **SQL Query**:
  ```sql
  SELECT
    (SELECT COUNT(*) FROM `bigquery-public-data.thelook_ecommerce.orders`) AS total_orders,
    (SELECT ROUND(SUM(sale_price), 2) FROM `bigquery-public-data.thelook_ecommerce.order_items`) AS total_revenue
  ```
- **Calculation**:
  - `avg_order_value = round(total_revenue / total_orders, 2)` if `total_orders > 0` else `0.0`.
- **Output Format**: `dict` containing `{"total_orders": int, "total_revenue": float, "avg_order_value": float, "data_source": "BigQuery"}`.

## Error Handling & Types
- BigQuery query result rows converted cleanly to native Python types (`str`, `float`, `int`).
- Handles potential missing/null values safely.
