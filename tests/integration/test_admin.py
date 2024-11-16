import pytest
import  json
from tests.conftest import admin

from config import settings
from common.logger import logger


#admin login and password
pytest.login = settings.test_admin_login
pytest.password = settings.test_admin_password

'''
def test_create_franchise(admin):
    """Return a new registered user."""

    phone = "+79567809696"
    password = "d171c9c34404d0230eabcd193Cff490c4d2f89f3c34df774d383c8617345a954"
    role = 6
    surname = "string"
    name = "string"
    referal_code = None
    id_city = []
'''

@pytest.mark.asyncio
@pytest.mark.dependency()
async def test_create_other_parametrs_of_drive(admin):
    new_service = {"title": "test_service", "amount": 1337}
    new_service_json = json.dumps(new_service)
    response = await admin.conn.post("/admins/other-parametrs-of-drive", json=new_service)
    assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.dependency()
async def test_get_other_parametrs_of_drive(admin):
    response = await admin.conn.get("/static-data/other-parametrs-of-drive")
    assert response.status_code == 200
    test_service = None
    logger.debug(response.json())
    for service in response.json()['data']:
        if service["title"] == "test_service":
            test_service = service["id"]
    pytest.test_service = test_service



@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_create_other_parametrs_of_drive", "test_get_other_parametrs_of_drive"])
async def test_put_other_parametrs_of_drive(admin):
    test_service = pytest.test_service
    request = {
        "id": test_service,
        "title": "test_service",
        "amount": 1488
    }
    response = await admin.conn.put("/admins/other-parametrs-of-drive", json=request)
    logger.debug(response.content)
    assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_create_other_parametrs_of_drive", "test_get_other_parametrs_of_drive"])
async def test_delete_other_parametrs_of_drive(admin):
    test_service = pytest.test_service
    request = {"id": test_service}
    response = await admin.conn.delete("/admins/other-parametrs-of-drive", json=request)
    assert response.status_code == 200