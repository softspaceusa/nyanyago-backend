from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AutoNanny"
    ssl_certfile: str = "fullchain.pem"
    ssl_keyfile: str = "privkey.pem"
    port: int = 443
    log_level: str = "debug"

    class Config:
        env_file = ".env"


settings = Settings()
