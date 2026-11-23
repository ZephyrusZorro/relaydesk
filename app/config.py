from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RELAYDESK_", env_file=".env", extra="ignore")
    db_path: str = "data/relaydesk.db"
    internal_key: str = ""
    portal_key: str = ""
    n8n_url: str = "http://127.0.0.1:15678"
    ollama_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.2:3b"
    seed_demo: bool = True
    request_timeout: float = 240
