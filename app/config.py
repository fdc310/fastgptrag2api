from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    fastgpt_base_url: str = "http://localhost:3000"
    fastgpt_api_key: str = ""

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "fastgpt_rag"

    # API key for caller authentication (separate from FastGPT key)
    api_key: str = ""

    app_port: int = 8000
    app_workers: int = 1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
