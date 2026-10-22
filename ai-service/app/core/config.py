from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Personal CEO - AI Service"
    app_version: str = "1.0.0"
    backend_url: str = "http://localhost:8080"
    environment: str = "development"

    # LLM Provider: "ollama" | "openai" | "mock"
    llm_provider: str = "ollama"

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    # OpenAI / Compatible settings (e.g. Groq, OpenRouter)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None

    # Timezone
    timezone: str = "Asia/Kolkata"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
