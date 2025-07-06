from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration settings for the application.
    """

    # Example setting
    gemini_api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
