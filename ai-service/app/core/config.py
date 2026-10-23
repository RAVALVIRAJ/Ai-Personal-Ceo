from pydantic_settings import BaseSettings, SettingsConfigDict


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
+
+    # ----- NEW SETTINGS (default values) -----
+    app_mode: str = "local"  # live | local (label only, does not affect behaviour)
+    llm_fallback_provider: str = ""  # optional fallback provider name
+    llm_timeout_seconds: int = 60
+    status_timeout_seconds: int = 3
+    rate_limit_per_minute: int = 0  # 0 = disabled
+    ollama_num_ctx: int = 4096
+    ollama_keep_alive: str = "30m"
+
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
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
    # New settings
    app_mode: str = "local"
    llm_fallback_provider: str = ""
    llm_timeout_seconds: int = 60
    status_timeout_seconds: int = 3
    rate_limit_per_minute: int = 0
    ollama_num_ctx: int = 4096
    ollama_keep_alive: str = "30m""Asia/Kolkata"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
