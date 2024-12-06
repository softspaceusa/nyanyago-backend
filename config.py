import os

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    app_name: str = "AutoNanny"
    ssl_certfile: str = "fullchain.pem"
    ssl_keyfile: str = "privkey.pem"
    port: int = 4443
    log_level: str = "debug"
    report_file_path: str = "./"

    test_admin_login: str = os.environ.get("TEST_ADMIN_LOGIN")
    test_admin_password: str = os.environ.get("TEST_ADMIN_PASSWORD")
    test_franchise_admin_login: str = os.environ.get("TEST_FRANCHISE_ADMIN_LOGIN")
    test_franchise_admin_password: str = os.environ.get("TEST_FRANCHISE_ADMIN_PASSWORD")
    test_driver_login: str = os.environ.get("TEST_DRIVER_LOGIN")
    test_driver_password: str = os.environ.get("TEST_DRIVER_PASSWORD")


load_dotenv(dotenv_path="../../.env")
load_dotenv(dotenv_path="../.env")
load_dotenv(dotenv_path=".env")
settings = Settings()