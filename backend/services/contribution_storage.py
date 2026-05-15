"""ContributionStorage — thin wrapper around Supabase Storage for KG-contribution PDFs.

Uploads PDFs submitted through ``POST /api/contributions/upload`` to the
``kg-contributions`` bucket and hands the backend a signed URL it can return
to the frontend for in-browser preview.

If ``SUPABASE_URL`` or ``SUPABASE_SERVICE_ROLE_KEY`` is missing, the service
silently degrades to a local-filesystem fallback at
``/var/lib/eleutheria/contributions/{contribution_id}/{filename}`` with the
same API surface — useful in tests, local dev, and any environment that
isn't wired up to Supabase Storage. ``put_pdf`` then returns a ``file://``
URL and ``get_signed_url`` returns a 1-hour signed copy of that path (the
file path itself, since there's nothing to sign).
"""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ContributionStorage:
    """Supabase Storage REST client for KG contribution PDFs (with FS fallback)."""

    BUCKET = "kg-contributions"

    # Where the FS fallback writes blobs when Supabase isn't configured.
    _DEFAULT_FALLBACK_ROOT = Path("/var/lib/eleutheria/contributions")

    def __init__(
        self,
        supabase_url: str | None = None,
        service_role_key: str | None = None,
        *,
        fallback_root: Path | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._supabase_url = (supabase_url or "").rstrip("/") or None
        self._service_role_key = service_role_key or None
        self._fallback_root = fallback_root or self._DEFAULT_FALLBACK_ROOT
        self._http: httpx.AsyncClient | None = http_client

        if not (self._supabase_url and self._service_role_key):
            logger.info(
                "ContributionStorage: Supabase creds missing — using FS fallback at %s",
                self._fallback_root,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def put_pdf(
        self,
        *,
        contribution_id: str,
        filename: str,
        content: bytes,
        content_type: str = "application/pdf",
    ) -> str:
        """Upload ``content`` to ``{BUCKET}/{contribution_id}/{filename}``.

        Returns the storage path (``{contribution_id}/{filename}``) — never a
        URL — so callers store something portable in the DB.
        """
        path = self._object_path(contribution_id, filename)

        if not self._has_supabase():
            self._fs_write(path, content)
            return path

        url = f"{self._supabase_url}/storage/v1/object/{self.BUCKET}/{path}"
        async with self._client() as client:
            response = await client.post(
                url,
                content=content,
                headers={
                    "Authorization": f"Bearer {self._service_role_key}",
                    "Content-Type": content_type,
                    "x-upsert": "true",
                },
            )
        if response.status_code >= 300:
            logger.error(
                "Supabase upload failed (%s): %s", response.status_code, response.text
            )
            raise RuntimeError(
                f"Supabase Storage upload failed: {response.status_code}"
            )
        return path

    async def get_signed_url(self, path: str, ttl_seconds: int = 3600) -> str:
        """Return a signed URL for ``path`` valid for ``ttl_seconds`` seconds.

        For the FS fallback this is simply a ``file://`` URL — no signing
        happens, but the API surface stays identical for callers.
        """
        if not self._has_supabase():
            fs_path = self._fs_path(path)
            return f"file://{fs_path}"

        url = f"{self._supabase_url}/storage/v1/object/sign/{self.BUCKET}/{path}"
        async with self._client() as client:
            response = await client.post(
                url,
                json={"expiresIn": ttl_seconds},
                headers={
                    "Authorization": f"Bearer {self._service_role_key}",
                    "Content-Type": "application/json",
                },
            )
        if response.status_code >= 300:
            logger.error(
                "Supabase sign failed (%s): %s", response.status_code, response.text
            )
            raise RuntimeError(f"Supabase Storage sign failed: {response.status_code}")
        payload: dict[str, Any] = response.json()
        signed = payload.get("signedURL") or payload.get("signedUrl") or ""
        if not signed:
            raise RuntimeError("Supabase Storage returned an empty signed URL")
        if signed.startswith("/"):
            signed = f"{self._supabase_url}/storage/v1{signed}"
        return signed

    async def delete(self, path: str) -> None:
        """Remove the object at ``path``."""
        if not self._has_supabase():
            fs_path = self._fs_path(path)
            with contextlib.suppress(FileNotFoundError):
                fs_path.unlink()
            return

        url = f"{self._supabase_url}/storage/v1/object/{self.BUCKET}/{path}"
        async with self._client() as client:
            response = await client.delete(
                url,
                headers={"Authorization": f"Bearer {self._service_role_key}"},
            )
        if response.status_code >= 300 and response.status_code != 404:
            logger.error(
                "Supabase delete failed (%s): %s",
                response.status_code,
                response.text,
            )
            raise RuntimeError(
                f"Supabase Storage delete failed: {response.status_code}"
            )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _has_supabase(self) -> bool:
        return bool(self._supabase_url and self._service_role_key)

    def _client(self) -> Any:
        """Return an async-context-manager that yields an httpx.AsyncClient."""
        if self._http is not None:
            return _PassthroughClient(self._http)
        return httpx.AsyncClient(timeout=30.0)

    @staticmethod
    def _object_path(contribution_id: str, filename: str) -> str:
        safe_filename = filename.strip().replace("/", "_").replace("\\", "_")
        return f"{contribution_id}/{safe_filename}"

    def _fs_path(self, path: str) -> Path:
        return self._fallback_root / path

    def _fs_write(self, path: str, content: bytes) -> None:
        target = self._fs_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


class _PassthroughClient:
    """Adapter so an injected ``httpx.AsyncClient`` survives ``async with``.

    Without this, using the same client across multiple calls would close it
    after the first ``async with`` block exits.
    """

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self._client

    async def __aexit__(self, *_: Any) -> None:
        return None


# ----------------------------------------------------------------------
# Factory
# ----------------------------------------------------------------------


def get_contribution_storage() -> ContributionStorage:
    """Build a ContributionStorage from env (Supabase if available, else FS)."""
    return ContributionStorage(
        supabase_url=os.getenv("SUPABASE_URL"),
        service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    )


__all__ = ["ContributionStorage", "get_contribution_storage"]
