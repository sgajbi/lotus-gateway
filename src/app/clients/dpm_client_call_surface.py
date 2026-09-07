"""The transport calls every lotus-manage client mixin makes, declared once.

The DPM client is assembled from six mixins, one per lotus-manage aggregate, and
each of them calls the same four transport methods that `DpmClient` implements.
Each mixin used to re-declare those four signatures as its own
`NotImplementedError` stubs so it would type-check standalone -- six copies of
one contract, which drifted the moment a signature changed: adding `params` to
`_post` for the two query-mechanism POSTs meant editing the same stub in every
mixin that had one, and a mixin that was missed would have type-checked against
a transport that no longer existed.

Inheriting this instead means the signature is written where it is true. The
stubs stay abstract-by-convention rather than `abc.abstractmethod` because
nothing instantiates a mixin directly; `DpmClient` is the only concrete class
and its own definitions take precedence over these in the MRO.
"""

from typing import Any


class DpmClientCallSurfaceMixin:
    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        raise NotImplementedError

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    async def _put(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
        operation: str,
    ) -> tuple[int, dict[str, Any]]:
        raise NotImplementedError

    def _clean_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Drop unset optional filters so they are not sent as empty values."""

        return {key: value for key, value in params.items() if value is not None}
