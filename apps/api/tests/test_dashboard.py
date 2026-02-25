# apps/api/tests/test_dashboard.py
from fastapi.testclient import TestClient

from .conftest import make_csv_rows


def _seed_backtest(client: TestClient) -> int:
    client.post(
        "/quant/data/upload",
        data={"symbol": "MSFT", "timeframe": "1d"},
        files={"file": ("msft.csv", make_csv_rows(100), "text/csv")},
    )

    strategy = client.post(
        "/quant/strategies",
        json={
            "name": "MSFT SMA 8/21",
            "strategy_type": "sma_crossover",
            "symbol": "MSFT",
            "timeframe": "1d",
            "parameters_json": {"fast_window": 8, "slow_window": 21},
        },
    )
    sid = strategy.json()["id"]

    run = client.post("/quant/backtests/run", json={"strategy_id": sid})
    assert run.status_code == 200, run.text
    return run.json()["run"]["id"]


def test_dashboard_endpoints(auth_client: TestClient):
    run_id = _seed_backtest(auth_client)

    summary = auth_client.get("/quant/dashboard/summary")
    assert summary.status_code == 200, summary.text
    s = summary.json()
    assert s["strategies_count"] >= 1
    assert s["backtests_count"] >= 1
    assert s["latest_run_id"] == run_id

    risk = auth_client.get("/quant/dashboard/risk")
    assert risk.status_code == 200, risk.text
    r = risk.json()
    assert r["latest_run_id"] == run_id

    perf = auth_client.get("/quant/dashboard/performance")
    assert perf.status_code == 200, perf.text
    p = perf.json()
    assert p["latest_run_id"] == run_id
    assert isinstance(p["equity_curve"], list)
    assert isinstance(p["recent_runs"], list)