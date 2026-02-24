# apps/api/tests/test_data.py
from fastapi.testclient import TestClient

from .conftest import make_csv_rows


def test_upload_list_symbols_and_bars(auth_client: TestClient):
    csv_bytes = make_csv_rows(40)

    upload = auth_client.post(
        "/data/upload",
        data={"symbol": "AAPL", "timeframe": "1d"},
        files={"file": ("aapl.csv", csv_bytes, "text/csv")},
    )
    assert upload.status_code == 200, upload.text
    payload = upload.json()
    assert payload["rows_inserted"] == 40
    assert payload["rows_skipped_duplicates"] == 0

    # Re-upload same file -> duplicates skipped
    upload2 = auth_client.post(
        "/data/upload",
        data={"symbol": "AAPL", "timeframe": "1d"},
        files={"file": ("aapl.csv", csv_bytes, "text/csv")},
    )
    assert upload2.status_code == 200, upload2.text
    payload2 = upload2.json()
    assert payload2["rows_inserted"] == 0
    assert payload2["rows_skipped_duplicates"] == 40

    symbols = auth_client.get("/data/symbols")
    assert symbols.status_code == 200, symbols.text
    assert {"symbol": "AAPL", "timeframe": "1d"} in symbols.json()

    bars = auth_client.get("/data/bars", params={"symbol": "AAPL", "timeframe": "1d", "limit": 10})
    assert bars.status_code == 200, bars.text
    rows = bars.json()
    assert len(rows) == 10
    assert rows[0]["symbol"] == "AAPL"
    assert "close" in rows[0]