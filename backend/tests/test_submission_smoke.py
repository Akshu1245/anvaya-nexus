from backend.anvaya import create_app


def test_public_demo_runs_the_submission_golden_path_and_generates_native_pdf():
    app = create_app(
        "testing",
        {
            "PUBLIC_DEMO_MODE": True,
            "DEMO_PASSWORD": "synthetic-only-demo-password",
        },
    )
    client = app.test_client()
    try:
        assert client.post("/api/auth/public-demo").status_code == 200

        investigation = client.post(
            "/api/investigations",
            json={
                "title": "Submission smoke test",
                "purpose": "Active Case Investigation",
                "selected_sources": ["CCTNS_REPLICA"],
            },
        )
        assert investigation.status_code == 201
        investigation_id = investigation.json["data"]["id"]

        preview = client.post(
            f"/api/investigations/{investigation_id}/query/preview",
            json={"query": "Find unresolved chain snatching at SYN-STN-01"},
        )
        assert preview.status_code == 200
        plan = preview.json["data"]["normalised_interpretation"]
        assert plan["intent"] == "SEARCH"

        search = client.post(f"/api/investigations/{investigation_id}/search", json=plan)
        assert search.status_code == 200
        assert search.json["data"]["result_count"] > 0
        case_id = search.json["data"]["results"][0]["case_id"]

        case_360 = client.get(
            f"/api/investigations/{investigation_id}/cases/{case_id}/360?sources=CCTNS_REPLICA"
        )
        assert case_360.status_code == 200
        assert case_360.json["data"]["case"]["id"] == case_id

        dossier = client.get(f"/api/investigations/{investigation_id}/cases/{case_id}/brief.pdf")
        assert dossier.status_code == 200
        assert dossier.mimetype == "application/pdf"
        assert dossier.data.startswith(b"%PDF")
    finally:
        app.extensions["repository"].close()
