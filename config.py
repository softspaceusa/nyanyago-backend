from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AutoNanny"
    db_user: str
    db_password: str
    db_host: str
    db_name: str
    ssl_certfile: str = "fullchain.pem"
    ssl_keyfile: str = "privkey.pem"
    port: int = 443
    log_level: str = "debug"

    class Config:
        env_file = ".env"


settings = Settings()
