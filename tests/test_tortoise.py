import pytest

from common.logger import logger
from config import settings
from models.users_db import UsersFranchiseUser

#admin login and password
pytest.login = settings.test_admin_login
pytest.password = settings.test_admin_password


@pytest.mark.asyncio
async def test_create_other_parametrs_of_drive(admin):
    data = await UsersFranchiseUser.filter().all().values()
    logger.debug(str(data))