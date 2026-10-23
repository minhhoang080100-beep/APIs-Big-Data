"""Catalog errors retain server diagnostics without disclosing SQL to clients."""

import logging

import pytest

from test_vietsun_scope import api


CATALOG_ROUTES = [
    ("/api/customers", "object"),
    ("/api/customers/OFFLINE", "object"),
    ("/api/cargoCategory", "object"),
    ("/api/cargoCategory/1", "object"),
    ("/api/cargoType", "object"),
    ("/api/cargoType/1040", "object"),
    ("/api/handlingMethodList", "object"),
    ("/api/handlingMethodList/OFFLINE", "object"),
    ("/api/class", "object"),
    ("/api/class/1", "object"),
    ("/api/shipDetails", "object"),
    ("/api/shipDetails/1234567", "object"),
    ("/api/origins", "string"),
    ("/api/origins/1", "string"),
    ("/api/containerSize", "object"),
]


@pytest.mark.parametrize("path,detail_shape", CATALOG_ROUTES)
def test_catalog_sql_errors_are_private_with_existing_500_shape(api, caplog, path, detail_shape):
    client, execute = api
    # Deliberately synthetic diagnostic, never read from environment or DB.
    diagnostic = "OFFLINE_SQL_DETAIL [08001] SERVER=private-test; SELECT secret_column FROM internal_table"
    execute.side_effect = RuntimeError(diagnostic)
    with caplog.at_level(logging.ERROR):
        response = client.get(path)

    assert response.status_code == 500
    assert "OFFLINE_SQL_DETAIL" not in response.text
    assert "08001" not in response.text
    assert "private-test" not in response.text
    assert "SELECT" not in response.text
    assert "secret_column" not in response.text
    assert "internal_table" not in response.text
    assert diagnostic in caplog.text
    assert execute.call_count == 1

    payload = response.json()
    assert set(payload) == {"detail"}
    if detail_shape == "string":
        assert payload["detail"] == "Lỗi lấy dữ liệu"
    else:
        assert set(payload["detail"]) == {"code", "message"}
        assert payload["detail"]["code"] == "0"
        expected = "Lỗi hệ thống" if path == "/api/containerSize" else "Lỗi lấy dữ liệu"
        assert payload["detail"]["message"] == expected
