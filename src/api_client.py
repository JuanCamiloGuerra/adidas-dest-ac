"""Cliente HTTP robusto para la API REST de SportRetail LAM.

Entradas: URL base, endpoint, parámetros y configuración de reintentos.
Salidas: respuestas JSON validadas y colecciones paginadas completas.
Dependencias: requests y logging.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class APIClientError(RuntimeError):
    """Error controlado de transporte, estado HTTP o contrato de respuesta."""


class SportRetailAPIClient:
    """Encapsula consultas HTTP y paginación defensiva."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        logger: logging.Logger | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logger or logging.getLogger("sportretail")
        self.session = session or requests.Session()
        if session is None:
            retry = Retry(
                total=max_retries,
                connect=max_retries,
                read=max_retries,
                status=max_retries,
                backoff_factor=0.4,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset({"GET"}),
                raise_on_status=False,
            )
            self.session.mount("http://", HTTPAdapter(max_retries=retry))
            self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def get_json(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Ejecuta GET y valida que la respuesta exitosa sea un objeto JSON."""

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            self.logger.error("Fallo de red en %s: %s", url, exc)
            raise APIClientError(f"No fue posible consultar {url}") from exc
        if response.status_code != 200:
            self.logger.error("Estado HTTP %s en %s", response.status_code, response.url)
            raise APIClientError(f"HTTP {response.status_code} al consultar {response.url}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise APIClientError(f"Respuesta no JSON en {response.url}") from exc
        if not isinstance(payload, dict):
            raise APIClientError(f"Se esperaba un objeto JSON en {response.url}")
        return payload

    def health(self) -> dict[str, Any]:
        """Valida disponibilidad y contrato mínimo de `/health`."""

        payload = self.get_json("/health")
        if payload.get("status") != "ok" or not isinstance(payload.get("records"), dict):
            raise APIClientError("La API respondió, pero /health no cumple el contrato esperado")
        return payload

    def get_paginated(
        self,
        endpoint: str,
        collection_key: str,
        params: dict[str, Any] | None = None,
        limit: int = 37,
        max_pages: int = 10_000,
    ) -> list[dict[str, Any]]:
        """Recupera una colección completa usando `total`, `skip` y `limit`.

        El desplazamiento avanza por el número real de registros recibidos; esto
        evita saltos si el servidor entrega menos elementos que el límite pedido.
        """

        if limit < 1:
            raise ValueError("limit debe ser mayor que cero")
        base_params = dict(params or {})
        base_params.pop("skip", None)
        base_params.pop("limit", None)
        records: list[dict[str, Any]] = []
        skip = 0
        expected_total: int | None = None
        for page_number in range(1, max_pages + 1):
            payload = self.get_json(endpoint, {**base_params, "skip": skip, "limit": limit})
            required = {"total", "skip", "limit", collection_key}
            missing = required.difference(payload)
            if missing:
                raise APIClientError(f"Faltan campos {sorted(missing)} en {endpoint}")
            page = payload[collection_key]
            total = payload["total"]
            if not isinstance(page, list) or not isinstance(total, int) or total < 0:
                raise APIClientError(f"Estructura paginada inválida en {endpoint}")
            if expected_total is None:
                expected_total = total
            elif total != expected_total:
                raise APIClientError(f"El total cambió durante la paginación de {endpoint}")
            if payload["skip"] != skip:
                raise APIClientError(f"La API devolvió skip={payload['skip']} cuando se solicitó {skip}")
            if not page and len(records) < total:
                raise APIClientError(f"Página vacía prematura en {endpoint} (skip={skip})")
            if not all(isinstance(item, dict) for item in page):
                raise APIClientError(f"La colección {collection_key} contiene elementos no válidos")
            records.extend(page)
            self.logger.info(
                "Extracción %s: página %s, recuperados %s/%s",
                endpoint,
                page_number,
                len(records),
                total,
            )
            if len(records) >= total:
                break
            skip += len(page)
            time.sleep(0.02)
        else:
            raise APIClientError(f"Se excedió max_pages={max_pages} en {endpoint}")
        if expected_total is None or len(records) != expected_total:
            raise APIClientError(
                f"Conteo inconsistente en {endpoint}: recuperados={len(records)}, total={expected_total}"
            )
        return records

