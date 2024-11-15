from typing import Generator, List
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from tortoise.contrib.fastapi import register_tortoise

from main import app

app_base_url = "https://127.0.0.1:4443/api/v1.0"
db_url = "postgres://api_auto_nanny:8yWcJm48c37@127.0.0.1:5432/api_nanny"


@dataclass
class TestUser:
    phone: str
    token: str
    conn: TestClient


@pytest.fixture(scope="function")
def conn() -> Generator:
    register_tortoise(
        app,
        db_url=db_url,
        modules={"models": ["models.authentication_db", "models.files_db", "models.users_db", "models.drivers_db",
                            "models.static_data_db", "models.chats_db", "models.admins_db", "models.orders_db"]},
        generate_schemas=True,
        add_exception_handlers=True
    )
    login = pytest.login
    password = pytest.password
    fbid = "fbid"

    with TestClient(app=app, base_url=app_base_url) as client:
        login_response = client.post("/api/v1.0/auth/login", json=dict(
            login=login,
            password=password,
            fbid=fbid))
    token = login_response.json()['token']
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app=app, base_url=app_base_url, headers=headers) as client:
        yield TestUser(
            phone = login,
            token = token,
            conn = client
        )

admin = franchise = parrent = conn
