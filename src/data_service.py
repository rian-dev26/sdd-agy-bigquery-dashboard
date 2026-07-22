import os
import pandas as pd
from pathlib import Path
from google.cloud import bigquery

DATA_DIR = Path(__file__).parent.parent / "data"
DATASET_ID = "bigquery-public-data.thelook_ecommerce"

_client = None


def get_bigquery_client() -> bigquery.Client:
    global _client
    if _client is None:
        project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "bigquery-public-data"
        _client = bigquery.Client(project=project_id)
    return _client



def get_revenue_trend() -> list[dict]:
    orders = pd.read_csv(DATA_DIR / "orders.csv", parse_dates=["created_at"])
    items = pd.read_csv(DATA_DIR / "order_items.csv")

    completed = orders[orders["status"] == "Complete"]
    merged = items.merge(
        completed[["order_id", "created_at"]],
        on="order_id",
        suffixes=("_item", ""),
    )
    merged["date"] = merged["created_at"].dt.date

    daily = merged.groupby("date")["sale_price"].sum().reset_index()
    daily.columns = ["date", "revenue"]
    daily = daily.sort_values("date")

    return [
        {"date": str(row["date"]), "revenue": round(row["revenue"], 2)}
        for _, row in daily.iterrows()
    ]


def get_top_products(limit: int = 10) -> list[dict]:
    items = pd.read_csv(DATA_DIR / "order_items.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")

    merged = items.merge(products, left_on="product_id", right_on="id", suffixes=("_item", "_product"))
    product_sales = (
        merged.groupby(["product_id", "name"])["sale_price"]
        .agg(["sum", "count"])
        .reset_index()
    )
    product_sales.columns = ["product_id", "name", "total_revenue", "units_sold"]
    product_sales = product_sales.sort_values("total_revenue", ascending=False).head(limit)

    return [
        {
            "name": row["name"],
            "total_revenue": round(row["total_revenue"], 2),
            "units_sold": int(row["units_sold"]),
        }
        for _, row in product_sales.iterrows()
    ]


def get_order_status_breakdown() -> list[dict]:
    orders = pd.read_csv(DATA_DIR / "orders.csv")
    status_counts = orders["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]

    return [
        {"status": row["status"], "count": int(row["count"])}
        for _, row in status_counts.iterrows()
    ]


def get_category_performance() -> list[dict]:
    items = pd.read_csv(DATA_DIR / "order_items.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")

    merged = items.merge(products, left_on="product_id", right_on="id", suffixes=("_item", "_product"))
    category_sales = (
        merged.groupby("category")["sale_price"]
        .agg(["sum", "count"])
        .reset_index()
    )
    category_sales.columns = ["category", "total_revenue", "units_sold"]
    category_sales = category_sales.sort_values("total_revenue", ascending=False)

    return [
        {
            "category": row["category"],
            "total_revenue": round(row["total_revenue"], 2),
            "units_sold": int(row["units_sold"]),
        }
        for _, row in category_sales.iterrows()
    ]


def get_dashboard_summary() -> dict:
    orders = pd.read_csv(DATA_DIR / "orders.csv")
    items = pd.read_csv(DATA_DIR / "order_items.csv")

    total_orders = len(orders)
    total_revenue = round(items["sale_price"].sum(), 2)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "data_source": "CSV",
    }
