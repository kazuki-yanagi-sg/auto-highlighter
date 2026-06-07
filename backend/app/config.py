from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境変数で設定を受け取る。秘密情報は .env から読む。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./marker.db"
    # 注釈/分類に使うLLMプロバイダ: "ollama" | "gemini"
    llm_provider: str = "ollama"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    ollama_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "phi4"
    voicevox_url: str = "http://voicevox:50021"
    voicevox_speaker: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()
