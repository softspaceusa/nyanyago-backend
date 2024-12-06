import pytest
import  json
from tests.conftest import admin

from config import settings
from common.logger import logger


#admin login and password
pytest.login = settings.test_admin_login
pytest.password = settings.test_admin_password


@pytest.mark.asyncio
async def test_create_franchise(admin):
    """Return a new registered user."""
    new_user = {
        "phone": "+7 (956) 796 96 99",
        "password": "12311231",
        "role": 6,
        "surname": "string",
        "name": "string",
        "id_city": []
    }
    response = await admin.conn.post("/admins/new_user", json=new_user)
    logger.debug(response.json())
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_partner(admin):
    """Return a new registered user."""
    new_user = {
        "phone": "+7 (956) 796 96 92",
        "password": "12311231",
        "role": 5,
        "surname": "string",
        "name": "string",
        "referal_code": "1ABCD2ABCD3ABCD4ABCD5ABCD6ABCD12",
        "id_city": []
    }
    response = await admin.conn.post("/admins/new_user", json=new_user)
    logger.debug(response.json())
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_partner(admin):
    """Wrong referal code."""
    new_user = {
        "phone": "+7 (956) 796 96 93",
        "password": "12311231",
        "role": 5,
        "surname": "string",
        "name": "string",
        "referal_code": "1ABCD2ABCD3ABCD4ABCD5ABCD6ABCD1",
        "id_city": []
    }
    response = await admin.conn.post("/admins/new_user", json=new_user)
    logger.debug(response.json())
    assert response.status_code == 422



@pytest.mark.asyncio
async def test_create_franchise_nonvalid(admin):
    """Non valid password"""
    new_user = {
        "phone": "+7 (956) 796 96 96",
        "password": "123",
        "role": 6,
        "surname": "string",
        "name": "string",
        "referal_code": None,
        "id_city": []
    }
    response = await admin.conn.post("/admins/new_user", json=new_user)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_franchise_admins(admin):
    response = await admin.conn.get("/admins/franchise_admins")
    assert response.status_code == 200



@pytest.mark.asyncio
@pytest.mark.dependency()
async def test_create_other_parametrs_of_drive(admin):
    new_service = {"title": "test_service", "amount": 1337}
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