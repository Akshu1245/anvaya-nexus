from pathlib import Path

from backend.anvaya import create_app


def test_production_frontend_build_is_served():
    index = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "index.html"
    assert index.is_file(), "Run the frontend production build before this integration test"
    app = create_app("production", {
        "DATABASE_URL": "sqlite:///:memory:",
        "SESSION_SECRET": "test-only-production-session-secret-0001",
        "ALLOWED_ORIGINS": "https://anvaya.example.test",
    })
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert "ANVAYA" in response.get_data(as_text=True)
    app.extensions["repository"].close()
