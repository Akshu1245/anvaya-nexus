from copy import deepcopy

import pytest

from backend.anvaya.importers.fir_er_adapter import adapt_fir_er


@pytest.fixture
def fir_er_record():
    return {
        "synthetic_data_only": True,
        "fir_number": "SYN-FIR-ER-0001", "crime_number": "SYN-CRIME-ER-0001",
        "registered_at": "2026-07-01T12:00:00+00:00", "investigation_status": "UNRESOLVED",
        "police_station": {"id": "SYN-UNIT-01"}, "district": {"id": "SYN-DIST-01"}, "state": {"id": "SYN-STATE-01"},
        "occurrence": {"from_at": "2026-07-01T10:00:00+00:00", "to_at": "2026-07-01T10:15:00+00:00", "location": {"id": "SYN-LOC-01", "locality": "Synthetic Ward"}},
        "sections": [{"id": "SYN-CLS-01", "act_id": "SYN-ACT-01", "section_id": "SYN-SEC-01", "source_record_id": "SYN-SR-SECTION-01"}],
        "people": [{"id": "SYN-PER-01", "role": "COMPLAINANT", "display_name": "Synthetic Person 01", "source_record_id": "SYN-SR-PERSON-01"}],
        "vehicles": [{"id": "SYN-VEH-01", "registration": "SYN-REG-000001", "type": "SYNTHETIC_TWO_WHEELER"}],
        "properties": [{"id": "SYN-PROP-01", "description": "Synthetic property identifier"}],
        "evidence": [{"id": "SYN-EVD-01", "description": "Synthetic evidence"}],
        "brief_facts": "Synthetic FIR ER-like narrative.",
        "source": {"system_id": "SYN-FIR-ER-SOURCE", "record_id": "SYN-SR-FIR-ER-0001", "external_id": "SYN-EXT-FIR-ER-0001", "version": "synthetic-1", "updated_at": "2026-07-01T12:00:00+00:00"},
    }


def test_valid_mapping_is_deterministic_and_canonical(fir_er_record):
    first = adapt_fir_er(fir_er_record)
    assert first == adapt_fir_er(fir_er_record)
    assert first["case"]["fir_number"] == "SYN-FIR-ER-0001"
    assert first["case_person_roles"][0]["role"] == "COMPLAINANT"
    assert first["case_legal_sections"][0]["section_id"] == "SYN-SEC-01"
    assert first["evidence_records"][1]["evidence_type"] == "SYNTHETIC_PROPERTY_REFERENCE"


def test_missing_fir_number_is_rejected(fir_er_record):
    fir_er_record.pop("fir_number")
    with pytest.raises(ValueError, match="fir_number is required"):
        adapt_fir_er(fir_er_record)


@pytest.mark.parametrize("field,value", [("registered_at", "not-a-date"), ("occurrence.from_at", "2026/07/01")])
def test_malformed_dates_are_rejected(fir_er_record, field, value):
    target = fir_er_record
    parts = field.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    with pytest.raises(ValueError, match="ISO 8601"):
        adapt_fir_er(fir_er_record)


def test_duplicate_identifiers_are_rejected(fir_er_record):
    fir_er_record["people"].append(deepcopy(fir_er_record["people"][0]))
    with pytest.raises(ValueError, match="duplicate identifier"):
        adapt_fir_er(fir_er_record)


def test_synthetic_marker_is_required(fir_er_record):
    fir_er_record["synthetic_data_only"] = False
    with pytest.raises(ValueError, match="synthetic_data_only"):
        adapt_fir_er(fir_er_record)


def test_provenance_is_retained(fir_er_record):
    result = adapt_fir_er(fir_er_record)
    assert result["case"]["source_record_id"] == "SYN-SR-FIR-ER-0001"
    assert result["case_person_roles"][0]["source_record_id"] == "SYN-SR-PERSON-01"
    assert result["source_record"]["source_system_id"] == "SYN-FIR-ER-SOURCE"
    assert '"synthetic_data_only":true' in result["source_record"]["payload_json"]


def test_unsupported_fields_are_ignored_and_reported(fir_er_record):
    fir_er_record["biometric_template"] = "must-not-pass-through"
    result = adapt_fir_er(fir_er_record)
    assert result["unsupported_fields"] == ["biometric_template"]
    assert "must-not-pass-through" not in str(result)
