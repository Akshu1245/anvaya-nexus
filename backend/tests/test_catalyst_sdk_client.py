from __future__ import annotations

import pytest

from backend.anvaya.platform.catalyst_errors import CatalystClientFailure
from backend.anvaya.platform.catalyst_sdk_client import CatalystSdkDataStoreClient
from backend.anvaya.repositories.catalyst_binding import bind_parameters
from backend.anvaya.repositories.catalyst_templates import CatalystQueryName, CatalystQueryRequest, DEFAULT_CATALYST_TEMPLATES


class FakeZCQL:
    def __init__(self, result):
        self.result = result
        self.queries = []

    def execute_query(self, query):
        self.queries.append(query)
        return self.result


class FakeCatalystApp:
    def __init__(self, result):
        self.service = FakeZCQL(result)

    def zcql(self):
        return self.service


def request_for(name, values):
    template = DEFAULT_CATALYST_TEMPLATES.get(name)
    return CatalystQueryRequest(template, bind_parameters(template, values))


def test_sdk_client_executes_only_allowlisted_source_system_list():
    app = FakeCatalystApp([{"source_systems": {"id": "CCTNS_REPLICA", "source_priority": "P0"}}])
    client = CatalystSdkDataStoreClient(lambda: app)
    envelope = client.execute_read(request_for(CatalystQueryName.SOURCE_SYSTEM_LIST, {"limit": 5}))
    assert envelope == {"status": "success", "data": [{"id": "CCTNS_REPLICA", "priority": "P0"}]}
    assert app.service.queries == [
        "SELECT id, name, source_tier, access_class, reliability_role, status, last_successful_sync, "
        "freshness_threshold_hours, version, connector_type, description, source_priority FROM "
        "source_systems ORDER BY source_priority ASC, id ASC LIMIT 0,5"
    ]


def test_sdk_client_quotes_canonical_id_and_rejects_unverified_queries():
    app = FakeCatalystApp([])
    client = CatalystSdkDataStoreClient(lambda: app)
    client.execute_read(request_for(CatalystQueryName.SOURCE_SYSTEM_BY_ID, {"id": "CCTNS_REPLICA"}))
    assert "WHERE id = 'CCTNS_REPLICA'" in app.service.queries[0]
    with pytest.raises(CatalystClientFailure) as error:
        client.execute_read(request_for(CatalystQueryName.CASE_BY_ID, {"id": "SYN-CASE-0001"}))
    assert error.value.category == "not_verified"


def test_sdk_client_health_and_writes_are_fail_closed():
    app = FakeCatalystApp([])
    client = CatalystSdkDataStoreClient(lambda: app)
    assert client.health_check() == {"status": "offline_ok"}
    assert app.service.queries == ["SELECT id FROM source_systems LIMIT 0,1"]
    with pytest.raises(CatalystClientFailure) as error:
        client.execute_write(request_for(CatalystQueryName.SOURCE_SYSTEM_LIST, {"limit": 1}))
    assert error.value.category == "unsupported_query"


def test_sdk_client_sanitizes_provider_failures():
    class BrokenZCQL:
        def execute_query(self, query):
            raise RuntimeError("provider secret detail")

    class BrokenApp:
        def zcql(self):
            return BrokenZCQL()

    client = CatalystSdkDataStoreClient(lambda: BrokenApp())
    with pytest.raises(CatalystClientFailure) as error:
        client.health_check()
    assert error.value.category == "unavailable"
    assert "provider secret detail" not in str(error.value)
