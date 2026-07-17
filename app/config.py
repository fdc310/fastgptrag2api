from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    fastgpt_base_url: str = "http://localhost:3000"
    fastgpt_api_key: str = ""

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "fastgpt_rag"

    # AES-256-CBC authentication
    aes_secret_key: str = ""          # 64-char hex (32 bytes)
    aes_token_ttl: int = 300          # seconds, timestamp validation window

    app_port: int = 8000
    app_workers: int = 1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
