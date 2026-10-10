from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from the environment / .env (git-ignored). Never hard-code keys."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # With DEMO_MODE=true nothing calls Reap or an LLM: recorded fixtures are used (demo_data).
    demo_mode: bool = True

    # Single place that pins the model ID used for signals; verify it exists with a spike.
    llm_model: str = "claude-sonnet-5-5"
    anthropic_api_key: str = ""

    reap_base_url: str = "https://sandbox.api.reap.global"
    reap_api_key: str = ""
    reap_version: str = ""  # value not in the public docs: get it from the API Reference or Telegram
    reap_return_url: str = "http://localhost:8000/return"  # Reap requires an HTTPS return URL


settings = Settings()
