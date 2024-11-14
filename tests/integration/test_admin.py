import pytest
from tests.conftest import admin, TestUser


#admin login and password
pytest.login = "+79259405489"
pytest.password = "5ad23bbcb26733b6a2dcad6a85f993ab"
def test_create_franchise(admin):
    """Return a new registered user."""

    phone = "+79567809696"
    password = "d171c9c34404d0230eabcd193Cff490c4d2f89f3c34df774d383c8617345a954"
    role = 6
    surname = "string"
    name = "string"
    referal_code = None
    id_city = []
