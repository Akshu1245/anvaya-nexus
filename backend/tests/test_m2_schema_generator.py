import json
import sqlite3

from backend.anvaya.services.generator import STORIES, generate, ground_truth_manifest


def test_schema_contains_all_m2_tables(app):
    rows=app.extensions["repository"].connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(); names={r[0] for r in rows}
    expected={"source_systems","source_records","transformation_events","cases","persons","aliases","organisations","phones","devices","vehicles","locations","documents","evidence_records","forensic_events","public_context","entity_edges","case_dna_features","trust_issues","import_jobs","import_failures"}
    assert expected<=names


def test_reduced_generator_is_deterministic():
    from backend.anvaya import create_app
    first=create_app("testing"); second=create_app("testing")
    a=generate(first.extensions["repository"],first.config,"test",1234); b=generate(second.extensions["repository"],second.config,"test",1234)
    assert a==b
    assert first.extensions["repository"].connection.execute("SELECT checksum FROM source_records ORDER BY id").fetchall()==second.extensions["repository"].connection.execute("SELECT checksum FROM source_records ORDER BY id").fetchall()
    first.extensions["repository"].close();second.extensions["repository"].close()


def test_full_generator_target_ranges(app):
    counts=generate(app.extensions["repository"],app.config,"full")
    assert 800<=counts["cases"]<=1200
    assert 1200<=counts["persons"]+counts["aliases"]<=1800
    assert 400<=counts["vehicles"]<=600
    assert 700<=counts["phones"]+counts["devices"]<=1000
    assert 300<=counts["locations"]<=500
    assert 800<=counts["evidence_records"]+counts["forensic_events"]<=1200
    assert 2000<=counts["entity_edges"]<=3500
    relational=sum(counts[key] for key in ("cases","persons","aliases","organisations","documents","vehicles","phones","devices","locations","evidence_records","forensic_events","entity_edges","case_dna_features"))
    assert 5000<=relational<=9000


def test_six_curated_stories_and_ground_truth_are_separate():
    assert len(STORIES)==6
    assert {s["type"] for s in STORIES}=={"true_hard_identifier","behavioural_similarity_unconfirmed","vehicle_colour_conflict","duplicate_identifier","invalid_chronology","candidate_identity_conflict"}
    manifest=ground_truth_manifest()
    assert manifest["later_action_expectation"]["highest_priority"]=="REVIEW_CCTV"
    assert "missing_source" in manifest["seeded_defects"]


def test_source_records_are_immutable_and_transformations_separate(app):
    generate(app.extensions["repository"],app.config,"test")
    conn=app.extensions["repository"].connection; record=conn.execute("SELECT id FROM source_records LIMIT 1").fetchone()[0]
    assert conn.execute("SELECT COUNT(*) FROM transformation_events WHERE source_record_id=?",(record,)).fetchone()[0]>=1
    try: conn.execute("UPDATE source_records SET version='changed' WHERE id=?",(record,))
    except sqlite3.IntegrityError as error: assert "immutable" in str(error)
    else: raise AssertionError("source record update should fail")


def test_all_generated_factual_rows_have_source_provenance(app):
    generate(app.extensions["repository"],app.config,"test")
    for table in ("cases","persons","aliases","organisations","phones","devices","vehicles","locations","documents","evidence_records","forensic_events","public_context","entity_edges","case_dna_features"):
        assert app.extensions["repository"].connection.execute(f"SELECT COUNT(*) FROM {table} WHERE source_record_id IS NULL").fetchone()[0]==0
