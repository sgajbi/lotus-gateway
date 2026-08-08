"""Governed caller fixtures shared by DPM router integration tests."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

DPM_CALLER_HEADERS = {
    "X-Actor-Id": "pm_sg_001",
    "X-Tenant-Id": "tenant-sg",
    "X-Role": "PORTFOLIO_MANAGER",
    "X-Region": "APAC",
}


def governed_dpm_client(application: FastAPI) -> TestClient:
    return TestClient(application, headers=DPM_CALLER_HEADERS)
