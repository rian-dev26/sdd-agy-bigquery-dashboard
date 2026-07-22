# 📊 E-commerce Analytics Dashboard

> A modern, real-time web application built with **FastAPI**, **Jinja2**, and **Google BigQuery**, fully containerized and ready for **Google Cloud Run** deployment.

---

## 🌟 Features

- **Live BigQuery Integration**: Queries Google Cloud's public dataset (`bigquery-public-data.thelook_ecommerce`).
- **Real-time Analytics**:
  - 📈 **Revenue Trends**: Tracks completed order revenue over time.
  - 🏆 **Top Selling Products**: Identifies top products by total revenue and units sold.
  - 📦 **Order Status Breakdown**: Visualizes order fulfillment states (Complete, Processing, Shipped, Cancelled, Returned).
  - 🏷️ **Category Performance**: Measures performance across product categories.
  - 📊 **Executive Summary**: High-level KPIs including Total Revenue, Total Orders, and Average Order Value (AOV).
- **Cloud Run Ready**: Containerized with Docker and configured for serverless auto-scaling on GCP.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, [FastAPI](https://fastapi.tiangolo.com/)
- **Templating & UI**: Jinja2, HTML5, Vanilla CSS
- **Data Warehouse**: [Google BigQuery](https://cloud.google.com/bigquery) (`bigquery-public-data.thelook_ecommerce`)
- **Containerization**: Docker, Google Cloud Build
- **Deployment Platform**: [Google Cloud Run](https://cloud.google.com/run)

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python `>= 3.11`
- [`uv`](https://docs.astral.sh/uv/) package manager (or `pip`)
- Google Cloud SDK (`gcloud`) authenticated to GCP

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd sdd-agy-bigquery-dashboard
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Authenticate Google Cloud:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

4. **Run the development server:**
   ```bash
   uv run uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
   ```

5. **Open in browser:**
   Navigate to `http://localhost:8080`.

---

## 🐳 Docker Setup

Build and run locally using Docker:

```bash
# Build Docker image
docker build -t bigquery-dashboard .

# Run Docker container
docker run -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID" \
  -v ~/.config/gcloud:/root/.config/gcloud \
  bigquery-dashboard
```

---

## ☁️ Deploy to Google Cloud Run

To deploy the application as a publicly accessible serverless service on Cloud Run:

```bash
# Enable required Google Cloud APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com --quiet

# Deploy to Cloud Run from source
gcloud run deploy bigquery-dashboard \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --quiet
```

---

## 📁 Project Structure

```text
.
├── Dockerfile              # Docker container build instructions
├── pyproject.toml          # Project metadata & Python dependencies
├── README.md               # Project documentation
└── src/
    ├── main.py             # FastAPI entrypoint & route handlers
    ├── data_service.py     # BigQuery query client & data aggregation logic
    ├── static/             # CSS stylesheet & static assets
    └── templates/          # Jinja2 HTML templates
```
