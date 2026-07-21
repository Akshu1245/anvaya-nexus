"""Dataset-focused Case 360 contract: additive, factual, and payload-safe."""

from backend.anvaya.services.investigation import CASE_360_SECTION_ORDER, case_360
from backend.anvaya.services.generator import generate


def _detail(app, case_id="SYN-CASE-0001"):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    return case_360(repository, user, "Active Case Investigation", case_id)


def test_dataset_case_360_has_ordered_sections_and_all_fir_data(app):
    detail = _detail(app)
    assert detail["sections"] == [{"id": key, "label": label} for key, label in CASE_360_SECTION_ORDER]
    assert detail["case"]["crime_number"]
    assert detail["case"]["case_number"]
    assert detail["incident"]["brief_facts"]
    assert {"complainants", "victims", "accused", "witnesses"} == set(detail["people"])
    assert detail["legal_provisions"]["associations"]
    assert detail["classification"]["canonical_status"]
    assert detail["police_and_court"]["unit_name"]
    assert detail["arrest_section"]["events"]
    assert detail["chargesheet_section"]["records"]
    assert detail["evidence_section"]["records"] == detail["evidence"]
    assert detail["data_quality"] == detail["trust_issues"]
    assert "entities" not in detail
    assert all({"age_years", "gender_code", "phone", "imei", "vehicle_registration"}.isdisjoint(person) for group in detail["people"].values() for person in group)
    assert [(event["at"], event["kind"], event["id"]) for event in detail["timeline"]] == sorted(
        (event["at"], event["kind"], event["id"]) for event in detail["timeline"]
    )


def test_case_360_provenance_is_safe_and_empty_sections_are_explicit(app):
    detail = _detail(app, "SYN-CASE-0001")
    source = detail["sources"][0]
    assert source["available"] is True
    assert "payload_json" not in source and "original_source_value" not in source and "checksum" not in source
    assert detail["source_records"] == detail["sources"]
    assert isinstance(source["transformation_history"], list)
    # At least one synthetic FIR intentionally has no optional court or events;
    # the view keeps section data as empty arrays instead of failing the response.
    repository = app.extensions["repository"]
    user = repository.find_user_by_id("SYN-USR-INV")
    empty = next(
        case["id"] for case in (repository.find_case_360_case(f"SYN-CASE-{number:04d}") for number in range(1, 31))
        if not repository.list_case_arrest_surrender_events(case["id"], source_system_ids=("CCTNS_REPLICA",))
    )
    empty_detail = case_360(repository, user, "Active Case Investigation", empty)
    assert empty_detail["arrest_section"]["events"] == []


def test_case_360_masks_coordinates_outside_assigned_jurisdiction(app):
    repository = app.extensions["repository"]
    generate(repository, app.config, "test")
    user = repository.find_user_by_id("SYN-USR-INV")
    external = next(
        case["id"] for case in (repository.find_case_360_case(f"SYN-CASE-{number:04d}") for number in range(1, 31))
        if case["station_id"] != user["assigned_station"] and case["latitude"] is not None
    )
    detail = case_360(repository, user, "Active Case Investigation", external)
    assert detail["incident"]["coordinates_masked"] is True
    assert detail["incident"]["latitude"] is None and detail["incident"]["longitude"] is None
    assert all("original_source_value" not in source for source in detail["sources"])
