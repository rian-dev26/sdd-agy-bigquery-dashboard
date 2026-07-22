import os
import subprocess
from google.cloud import bigquery

DATASET_ID = "bigquery-public-data.thelook_ecommerce"
_client = None


def get_bigquery_client() -> bigquery.Client:
    global _client
    if _client is None:
        project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id or project_id == "bigquery-public-data":
            try:
                res = subprocess.run(
                    ["gcloud", "config", "get-value", "project"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res.returncode == 0:
                    lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
                    if lines and lines[-1] != "(unset)":
                        project_id = lines[-1]
            except Exception:
                pass

        if project_id == "bigquery-public-data":
            project_id = None

        if project_id:
            _client = bigquery.Client(project=project_id)
        else:
            _client = bigquery.Client()
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
