"""WSGI entrypoint for a future Catalyst AppSail Development deployment."""
from backend.anvaya import create_app

app = create_app()
