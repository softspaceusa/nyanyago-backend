import pytest
from tests.conftest import admin, parrent
from common.logger import logger

from const.users_const import GetUserMoneySuccess

#admin login and password
pytest.login = "+79259405489"
pytest.password = "5ad23bbcb26733b6a2dcad6a85f993ab"

def test_get_money_by_admin(admin):
    json_req = {'limit': 30, 'offset': 0}
    money_resp = admin.conn.post("/api/v1.0/users/money?period=current_day", json=json_req)
    logger.debug(money_resp)
    assert money_resp.status_code == 200

#driver and parrent
pytest.login = "+79262713209"
pytest.password = "25d55ad283aa400af464c76d713c07ad"

def test_get_money_by_parrent(parrent):
    json_req = {'limit': 30, 'offset': 0}
    money_resp = parrent.conn.post("/api/v1.0/users/money?period=current_year", json=json_req)
    logger.debug(f"Get a next response {money_resp.json()}")
    assert GetUserMoneySuccess.model_validate(money_resp.json())
    assert money_resp.status_code == 200
