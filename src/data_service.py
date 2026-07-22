import os
import json
import subprocess
import logging
from pathlib import Path
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

DATASET_ID = "bigquery-public-data.thelook_ecommerce"
DEFAULT_PROJECT_ID = "sdd-agy-cli-d69221667e"
DATA_DIR = Path(__file__).parent.parent / "data"

_client = None


def get_bigquery_client() -> bigquery.Client:
    global _client
    if _client is None:
        sa_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") or os.getenv("GCP_SERVICE_ACCOUNT_KEY")
        if sa_json:
            info = json.loads(sa_json)
            credentials = service_account.Credentials.from_service_account_info(info)
            _client = bigquery.Client(credentials=credentials, project=credentials.project_id)
            return _client

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
            except Exception as e:
                logger.warning(f"Failed to get project from gcloud: {e}")

        if not project_id or project_id == "bigquery-public-data":
            project_id = DEFAULT_PROJECT_ID

        _client = bigquery.Client(project=project_id)
    return _client


# --- CSV Fallbacks ---

_dfs = {}


def get_csv_data():
    global _dfs
    if not _dfs:
        try:
            orders_df = pd.read_csv(DATA_DIR / "orders.csv")
            order_items_df = pd.read_csv(DATA_DIR / "order_items.csv")
            products_df = pd.read_csv(DATA_DIR / "products.csv")
            _dfs = {
                "orders": orders_df,
                "order_items": order_items_df,
                "products": products_df,
            }
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            _dfs = {}
    return _dfs


def get_revenue_trend_csv() -> list[dict]:
    dfs = get_csv_data()
    if not dfs:
        return []
    oi = dfs["order_items"].copy()
    o = dfs["orders"].copy()
    merged = oi.merge(o[o["status"] == "Complete"], on="order_id")
    merged["date"] = pd.to_datetime(merged["created_at_x"]).dt.strftime("%Y-%m-%d")
    grouped = merged.groupby("date")["sale_price"].sum().reset_index()
    grouped.sort_values("date", inplace=True)
    return [
        {"date": str(row["date"]), "revenue": round(float(row["sale_price"]), 2)}
        for _, row in grouped.iterrows()
    ]


def get_top_products_csv(limit: int = 10) -> list[dict]:
    dfs = get_csv_data()
    if not dfs:
        return []
    oi = dfs["order_items"].copy()
    p = dfs["products"].copy()
    merged = oi.merge(p, left_on="product_id", right_on="id")
    grouped = merged.groupby(["product_id", "name"]).agg(
        total_revenue=("sale_price", "sum"),
        units_sold=("id_x", "count")
    ).reset_index()
    grouped.sort_values("total_revenue", ascending=False, inplace=True)
    top = grouped.head(limit)
    return [
        {
            "name": row["name"],
            "total_revenue": round(float(row["total_revenue"]), 2),
            "units_sold": int(row["units_sold"]),
        }
        for _, row in top.iterrows()
    ]


def get_order_status_breakdown_csv() -> list[dict]:
    dfs = get_csv_data()
    if not dfs:
        return []
    o = dfs["orders"].copy()
    grouped = o["status"].value_counts().reset_index()
    grouped.columns = ["status", "count"]
    return [
        {"status": row["status"], "count": int(row["count"])}
        for _, row in grouped.iterrows()
    ]


def get_category_performance_csv() -> list[dict]:
    dfs = get_csv_data()
    if not dfs:
        return []
    oi = dfs["order_items"].copy()
    p = dfs["products"].copy()
    merged = oi.merge(p, left_on="product_id", right_on="id")
    grouped = merged.groupby("category").agg(
        total_revenue=("sale_price", "sum"),
        units_sold=("id_x", "count")
    ).reset_index()
    grouped.sort_values("total_revenue", ascending=False, inplace=True)
    return [
        {
            "category": row["category"],
            "total_revenue": round(float(row["total_revenue"]), 2),
            "units_sold": int(row["units_sold"]),
        }
        for _, row in grouped.iterrows()
    ]


def get_dashboard_summary_csv() -> dict:
    dfs = get_csv_data()
    if not dfs:
        return {"total_orders": 0, "total_revenue": 0.0, "avg_order_value": 0.0, "data_source": "Fallback"}
    o = dfs["orders"]
    oi = dfs["order_items"]
    total_orders = len(o)
    total_revenue = round(float(oi["sale_price"].sum()), 2)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "data_source": "Sample Dataset (CSV Fallback)",
    }


# --- Primary Query Functions with Fallbacks ---


def get_revenue_trend() -> list[dict]:
    try:
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
        res = [
            {"date": str(row["date"]), "revenue": float(row["revenue"])}
            for row in rows
        ]
        if res:
            return res
        return get_revenue_trend_csv()
    except Exception as e:
        logger.warning(f"BigQuery query failed, falling back to CSV: {e}")
        return get_revenue_trend_csv()


def get_top_products(limit: int = 10) -> list[dict]:
    try:
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
        res = [
            {
                "name": row["name"],
                "total_revenue": float(row["total_revenue"]),
                "units_sold": int(row["units_sold"]),
            }
            for row in rows
        ]
        if res:
            return res
        return get_top_products_csv(limit=limit)
    except Exception as e:
        logger.warning(f"BigQuery query failed, falling back to CSV: {e}")
        return get_top_products_csv(limit=limit)


def get_order_status_breakdown() -> list[dict]:
    try:
        client = get_bigquery_client()
        query = f"""
            SELECT
                status,
                COUNT(*) AS count
            FROM `{DATASET_ID}.orders`
            GROUP BY status
        """
        rows = client.query(query).result()
        res = [
            {"status": row["status"], "count": int(row["count"])}
            for row in rows
        ]
        if res:
            return res
        return get_order_status_breakdown_csv()
    except Exception as e:
        logger.warning(f"BigQuery query failed, falling back to CSV: {e}")
        return get_order_status_breakdown_csv()


def get_category_performance() -> list[dict]:
    try:
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
        res = [
            {
                "category": row["category"],
                "total_revenue": float(row["total_revenue"]),
                "units_sold": int(row["units_sold"]),
            }
            for row in rows
        ]
        if res:
            return res
        return get_category_performance_csv()
    except Exception as e:
        logger.warning(f"BigQuery query failed, falling back to CSV: {e}")
        return get_category_performance_csv()


def get_dashboard_summary() -> dict:
    try:
        client = get_bigquery_client()
        query = f"""
            SELECT
                (SELECT COUNT(*) FROM `{DATASET_ID}.orders`) AS total_orders,
                (SELECT ROUND(SUM(sale_price), 2) FROM `{DATASET_ID}.order_items`) AS total_revenue
        """
        rows = list(client.query(query).result())
        if not rows:
            return get_dashboard_summary_csv()

        row = rows[0]
        total_orders = int(row["total_orders"] or 0)
        total_revenue = float(row["total_revenue"] or 0.0)
        avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

        if total_orders == 0 and total_revenue == 0.0:
            return get_dashboard_summary_csv()

        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "avg_order_value": avg_order_value,
            "data_source": "BigQuery",
        }
    except Exception as e:
        logger.warning(f"BigQuery query failed, falling back to CSV: {e}")
        return get_dashboard_summary_csv()
