from flask import Blueprint

from backend.anvaya.api.errors import ApiError


def test_structured_not_found_error(client):
    response = client.get("/api/not-a-route")
    assert response.status_code == 404
    assert set(response.json) == {"request_id", "code", "message", "retryable"}
    assert response.json["code"] == "HTTP_404"
    assert response.json["retryable"] is False


def test_unexpected_error_hides_stack_trace(app):
    test_blueprint = Blueprint("test_errors", __name__)

    @test_blueprint.get("/api/test-error")
    def raise_error():
        raise RuntimeError("sensitive implementation detail")

    app.register_blueprint(test_blueprint)
    response = app.test_client().get("/api/test-error")
    assert response.status_code == 500
    assert response.json["code"] == "INTERNAL_ERROR"
    assert response.json["message"] == "An unexpected error occurred."
    assert "sensitive" not in response.get_data(as_text=True)


def test_api_error_uses_contract(app):
    test_blueprint = Blueprint("test_api_errors", __name__)

    @test_blueprint.get("/api/test-api-error")
    def raise_api_error():
        raise ApiError("FOUNDATION_TEST", "Safe test error.", 400, False)

    app.register_blueprint(test_blueprint)
    response = app.test_client().get("/api/test-api-error")
    assert response.status_code == 400
    assert response.json["code"] == "FOUNDATION_TEST"
    assert response.json["message"] == "Safe test error."
