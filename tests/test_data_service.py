import os
import pytest
from unittest.mock import MagicMock, patch
import src.data_service
from src.data_service import get_bigquery_client

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

