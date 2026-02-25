# apps/api/tests/test_strategies.py
from fastapi.testclient import TestClient


def test_strategy_crud(auth_client: TestClient):
    # Create
    create = auth_client.post(
        "/quant/strategies",
        json={
            "name": "SMA 10/20 AAPL",
            "strategy_type": "sma_crossover",
            "symbol": "aapl",
            "timeframe": "1d",
            "parameters_json": {"fast_window": 10, "slow_window": 20},
        },
    )
    assert create.status_code == 200, create.text
    s = create.json()
    assert s["symbol"] == "AAPL"
    strategy_id = s["id"]

    # List
    lst = auth_client.get("/quant/strategies")
    assert lst.status_code == 200, lst.text
    arr = lst.json()
    assert len(arr) == 1
    assert arr[0]["id"] == strategy_id

    # Get one
    one = auth_client.get(f"/quant/strategies/{strategy_id}")
    assert one.status_code == 200, one.text
    assert one.json()["name"] == "SMA 10/20 AAPL"

    # Update
    upd = auth_client.patch(
        f"/quant/strategies/{strategy_id}",
        json={"name": "SMA 5/30 AAPL", "parameters_json": {"fast_window": 5, "slow_window": 30}},
    )
    assert upd.status_code == 200, upd.text
    assert upd.json()["name"] == "SMA 5/30 AAPL"
    assert upd.json()["parameters_json"]["fast_window"] == 5

    # Delete
    delete = auth_client.delete(f"/quant/strategies/{strategy_id}")
    assert delete.status_code == 200, delete.text

    lst2 = auth_client.get("/quant/strategies")
    assert lst2.status_code == 200
    assert lst2.json() == []