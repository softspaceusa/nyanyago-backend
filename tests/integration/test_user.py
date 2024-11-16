import pytest
from tests.conftest import admin, parrent
from common.logger import logger

from config import settings
from const.users_const import GetUserMoneySuccess

#admin login and password
pytest.login = settings.test_admin_login
pytest.password = settings.test_admin_password

@pytest.mark.asyncio
async def test_get_money_by_admin(admin):
    json_req = {'limit': 30, 'offset': 0}
    money_resp = await admin.conn.post("/api/v1.0/users/money?period=current_day", json=json_req)
    logger.debug(money_resp)
    assert money_resp.status_code == 200

#driver and parrent
pytest.login = settings.test_driver_login
pytest.password = settings.test_driver_password

@pytest.mark.asyncio
async def test_get_money_by_parrent(parrent):
    json_req = {'limit': 30, 'offset': 0}
    money_resp = await parrent.conn.post("/api/v1.0/users/money?period=current_year", json=json_req)
    logger.debug(f"Get a next response {money_resp.json()}")
    assert GetUserMoneySuccess.model_validate(money_resp.json())
    assert money_resp.status_code == 200
