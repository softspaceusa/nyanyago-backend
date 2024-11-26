from typing import Generator, Union, Optional, Any
from dataclasses import dataclass
from asyncio import get_event_loop

import pytest
from httpx._client import UseClientDefault
from httpx._types import QueryParamTypes, HeaderTypes, CookieTypes, AuthTypes, TimeoutTypes, RequestExtensions
from typing_extensions import Self

from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient, URL, USE_CLIENT_DEFAULT, Response
from tortoise.contrib.fastapi import register_tortoise
from tortoise import Tortoise

from  common.logger import logger

app_base_url = "https://127.0.0.1:4443/api/v1.0"
db_url = "postgres://api_auto_nanny:8yWcJm48c37@127.0.0.1:5432/api_nanny"

from main import app

class TestClient(AsyncClient):
    def __init__(self, app, base_url="http://test", mount_lifespan=True, **kw) -> None:
        self.mount_lifespan = mount_lifespan
        self._manager: Optional[LifespanManager] = None
        super().__init__(transport=ASGITransport(app), base_url=base_url, **kw)

    async def __aenter__(self) -> Self:
        if self.mount_lifespan:
            app = self._transport.app  # type:ignore
            self._manager = await LifespanManager(app).__aenter__()
            self._transport = ASGITransport(app=self._manager.app)
        return await super().__aenter__()

    async def __aexit__(self, *args, **kw):
        await super().__aexit__(*args, **kw)
        if self._manager is not None:
            await self._manager.__aexit__(*args, **kw)

    async def delete(
            self,
            url: Union[URL, str],
            *,
            params: Union[QueryParamTypes, None] = None,
            headers: Union[HeaderTypes, None] = None,
            cookies: Union[CookieTypes, None] = None,
            json: Union[Any, None] = None,
            auth: Union[AuthTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
            follow_redirects: Union[bool, UseClientDefault] = USE_CLIENT_DEFAULT,
            timeout: Union[TimeoutTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
            extensions: Union[RequestExtensions, None] = None,
    ) -> Response:
        """
        Send a `DELETE` request.

        **Parameters**: See `httpx.request`.
        """
        return await self.request(
            "DELETE",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            json=json,
            auth=auth,
            follow_redirects=follow_redirects,
            timeout=timeout,
            extensions=extensions,
        )


@dataclass
class TestUser:
    phone: str
    token: str
    conn: AsyncClient


@pytest.fixture(scope="function")
async def conn() -> Generator:

    login = pytest.login
    password = pytest.password
    fbid = "fbid"

    async with TestClient(app=app, base_url=app_base_url) as client:
        login_response = await client.post("/auth/login", json=dict(
            login=login,
            password=password,
            fbid=fbid))
    logger.debug(login_response.json())
    token = login_response.json()['token']
    headers = {"Authorization": f"Bearer {token}"}

    async with TestClient(app=app, base_url=app_base_url, headers=headers) as client:
        yield TestUser(
            phone=login,
            token=token,
            conn=client
        )

admin = franchise = parrent = conn

@pytest.fixture(scope="session")
async def event_loop():
    loop = get_event_loop()
    yield loop