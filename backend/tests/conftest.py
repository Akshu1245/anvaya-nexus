import pytest

from backend.anvaya import create_app


@pytest.fixture()
def app():
    application = create_app("testing")
    yield application
    application.extensions["repository"].close()


@pytest.fixture()
def client(app):
    return app.test_client()
