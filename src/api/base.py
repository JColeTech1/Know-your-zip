"""
BaseAPIClient — shared HTTP client for all Miami-Dade ArcGIS data modules.

All domain API classes (education, healthcare, emergency, infrastructure, geo)
inherit from this class. No domain module should call requests.get directly.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from src.constants import (
    ARCGIS_BASE_URL,
    ARCGIS_QUERY_PARAMS,
    API_MAX_RETRIES,
    API_RETRY_BACKOFF_FACTOR,
    API_RETRY_DELAY_SECONDS,
    API_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


class ArcGISError(Exception):
    """Raised when an ArcGIS endpoint returns an error or unexpected response."""


class BaseAPIClient:
    """
    Shared HTTP client for all ArcGIS REST endpoint modules.

    Provides:
    - Persistent requests.Session with default headers
    - Retry loop with exponential back-off
    - Consistent timeout enforcement
    - Structured error logging
    """

    def __init__(self) -> None:
        self.base_url: str = ARCGIS_BASE_URL
        self.session: requests.Session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def fetch(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
        full_url: str | None = None,
    ) -> dict[str, Any]:
        """
        GET a single ArcGIS endpoint and return the parsed JSON body.

        Args:
            path: Service path relative to ARCGIS_BASE_URL
                  (e.g. "/SchoolSite_gdb/FeatureServer/0/query").
                  Ignored when full_url is provided.
            params: Query parameters merged with the standard ARCGIS_QUERY_PARAMS.
                    Caller-supplied values override defaults.
            full_url: Override to use an absolute URL (e.g. opendata endpoints).

        Returns:
            Parsed JSON dict from the ArcGIS response.

        Raises:
            ArcGISError: On HTTP error, timeout, or JSON decode failure after all retries.
        """
        url = full_url or f"{self.base_url}{path}"
        merged: dict[str, str] = {**ARCGIS_QUERY_PARAMS, **(params or {})}
        return self._get_with_retry(url, merged)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_with_retry(
        self,
        url: str,
        params: dict[str, str],
    ) -> dict[str, Any]:
        """Execute GET with retry + exponential back-off."""
        last_exc: Exception | None = None

        for attempt in range(1, API_MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=API_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]

            except requests.exceptions.Timeout as exc:
                last_exc = exc
                logger.warning("Timeout on attempt %d/%d for %s", attempt, API_MAX_RETRIES, url)

            except requests.exceptions.HTTPError as exc:
                last_exc = exc
                logger.warning(
                    "HTTP %s on attempt %d/%d for %s",
                    exc.response.status_code,
                    attempt,
                    API_MAX_RETRIES,
                    url,
                )

            except requests.exceptions.RequestException as exc:
                last_exc = exc
                logger.warning(
                    "Request error on attempt %d/%d for %s: %s",
                    attempt,
                    API_MAX_RETRIES,
                    url,
                    exc,
                )

            except ValueError as exc:
                # JSON decode failure — no point retrying
                raise ArcGISError(f"Invalid JSON from {url}: {exc}") from exc

            if attempt < API_MAX_RETRIES:
                delay = API_RETRY_DELAY_SECONDS * (API_RETRY_BACKOFF_FACTOR ** (attempt - 1))
                logger.info("Retrying in %.1f s…", delay)
                time.sleep(delay)

        raise ArcGISError(
            f"All {API_MAX_RETRIES} attempts failed for {url}"
        ) from last_exc
