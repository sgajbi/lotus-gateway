import json
from pathlib import Path
from typing import Any, TypeVar, cast

from pydantic import BaseModel, ValidationError

from app.contracts.domain_products import (
    DomainProductCatalogResponse,
    DomainProductDetailResponse,
    DomainProductGraphResponse,
    DomainProductTrustCertificationResponse,
)

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class DomainProductCatalogUnavailable(RuntimeError):
    """Raised when platform-generated catalog artifacts cannot serve discovery."""


class DomainProductNotFound(LookupError):
    """Raised when a requested governed domain product is not present in the catalog."""


class DomainProductCatalogService:
    def __init__(
        self,
        catalog_path: str,
        dependency_graph_path: str,
        live_trust_certification_path: str,
    ) -> None:
        self._catalog_path = Path(catalog_path)
        self._dependency_graph_path = Path(dependency_graph_path)
        self._live_trust_certification_path = Path(live_trust_certification_path)

    async def get_catalog(
        self,
        *,
        consumer_system: str,
        correlation_id: str,
    ) -> DomainProductCatalogResponse:
        catalog = self._load_json_object(self._catalog_path)
        return self._validate_response(
            DomainProductCatalogResponse,
            {
                "data": {
                    "consumerSystem": consumer_system,
                    "correlationId": correlation_id,
                    **catalog,
                }
            },
            self._catalog_path,
        )

    async def get_product(
        self,
        *,
        producer_repository: str,
        product_name: str,
        product_version: str,
        consumer_system: str,
        correlation_id: str,
    ) -> DomainProductDetailResponse:
        catalog = self._load_json_object(self._catalog_path)
        product = next(
            (
                candidate
                for candidate in catalog.get("products", [])
                if isinstance(candidate, dict)
                and candidate.get("producer_repository") == producer_repository
                and candidate.get("product_name") == product_name
                and candidate.get("product_version") == product_version
            ),
            None,
        )
        if product is None:
            product_key = f"{producer_repository}:{product_name}:{product_version}"
            raise DomainProductNotFound(product_key)

        return self._validate_response(
            DomainProductDetailResponse,
            {
                "data": {
                    "consumerSystem": consumer_system,
                    "correlationId": correlation_id,
                    "contractVersion": catalog.get("contract_version"),
                    "product": product,
                }
            },
            self._catalog_path,
        )

    async def get_dependency_graph(
        self,
        *,
        consumer_system: str,
        correlation_id: str,
    ) -> DomainProductGraphResponse:
        graph = self._load_json_object(self._dependency_graph_path)
        return self._validate_response(
            DomainProductGraphResponse,
            {
                "data": {
                    "consumerSystem": consumer_system,
                    "correlationId": correlation_id,
                    **graph,
                }
            },
            self._dependency_graph_path,
        )

    async def get_trust_certification(
        self,
        *,
        consumer_system: str,
        correlation_id: str,
    ) -> DomainProductTrustCertificationResponse:
        if not self._live_trust_certification_path.exists():
            return self._trust_unavailable_response(
                consumer_system=consumer_system,
                correlation_id=correlation_id,
                reason=(
                    "Platform live trust certification artifact is unavailable: "
                    f"{self._live_trust_certification_path}"
                ),
            )

        certification = self._load_json_object(self._live_trust_certification_path)
        summary = certification.get("summary")
        if not isinstance(summary, dict) or not isinstance(summary.get("certification_state"), str):
            raise DomainProductCatalogUnavailable(
                "Platform domain-product artifact failed gateway contract validation: "
                f"{self._live_trust_certification_path}"
            )
        trust_posture = summary["certification_state"]
        return self._validate_response(
            DomainProductTrustCertificationResponse,
            {
                "data": {
                    "consumerSystem": consumer_system,
                    "correlationId": correlation_id,
                    "trustAvailable": True,
                    "trustPosture": trust_posture,
                    "unavailableReason": None,
                    **certification,
                }
            },
            self._live_trust_certification_path,
        )

    def _trust_unavailable_response(
        self,
        *,
        consumer_system: str,
        correlation_id: str,
        reason: str,
    ) -> DomainProductTrustCertificationResponse:
        return DomainProductTrustCertificationResponse.model_validate(
            {
                "data": {
                    "consumerSystem": consumer_system,
                    "correlationId": correlation_id,
                    "trustAvailable": False,
                    "trustPosture": "unavailable",
                    "unavailableReason": reason,
                    "governedByRfcs": ["RFC-0087"],
                    "productCertifications": [],
                    "issues": [],
                }
            }
        )

    def _load_json_object(self, path: Path) -> dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except OSError as exc:
            raise DomainProductCatalogUnavailable(
                f"Platform domain-product artifact is unavailable: {path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise DomainProductCatalogUnavailable(
                f"Platform domain-product artifact is not valid JSON: {path}"
            ) from exc

        if not isinstance(payload, dict):
            raise DomainProductCatalogUnavailable(
                f"Platform domain-product artifact must be a JSON object: {path}"
            )

        return cast(dict[str, Any], payload)

    def _validate_response(
        self,
        model_type: type[ResponseModel],
        payload: dict[str, Any],
        path: Path,
    ) -> ResponseModel:
        try:
            return model_type.model_validate(payload)
        except ValidationError as exc:
            raise DomainProductCatalogUnavailable(
                f"Platform domain-product artifact failed gateway contract validation: {path}"
            ) from exc
