"""AppSail-specific Catalyst SDK initialization for Development read-only mode."""
from __future__ import annotations

from typing import Any, Callable

from flask import Flask, g, request

from backend.anvaya.platform.catalyst_errors import CatalystClientFailure
from backend.anvaya.platform.catalyst_sdk_client import CatalystSdkDataStoreClient


def configure_catalyst_appsail_runtime(app: Flask) -> None:
    """Install request-scoped SDK initialization and inject the read-only client.

    This function performs no provider call at startup. The SDK is initialized
    from the incoming request, as required by Catalyst AppSail's Python SDK.
    """
    if app.config.get("STORAGE_BACKEND") != "catalyst" or app.config.get("CATALYST_RUNTIME") != "appsail":
        return

    initializer = app.config.get("CATALYST_SDK_INITIALIZER") or _load_initializer()

    @app.before_request
    def initialize_catalyst_sdk() -> None:
        try:
            g.catalyst_app = initializer(req=request)
        except Exception as error:
            # Never expose SDK/provider details through startup or API errors.
            raise CatalystClientFailure("unavailable", True) from error

    def current_catalyst_app() -> Any:
        catalyst_app = getattr(g, "catalyst_app", None)
        if catalyst_app is None:
            raise CatalystClientFailure("not_configured", False)
        return catalyst_app

    app.config["CATALYST_DATASTORE_CLIENT"] = CatalystSdkDataStoreClient(current_catalyst_app)


def _load_initializer() -> Callable[..., Any]:
    try:
        import zcatalyst_sdk
    except ImportError as error:
        raise ValueError("Catalyst AppSail runtime requires the zcatalyst-sdk package") from error
    return zcatalyst_sdk.initialize
