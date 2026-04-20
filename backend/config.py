from __future__ import annotations

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


# Providers that the app supports. To add a new one (e.g. DeepSeek), append
# its id here + declare DEEPSEEK_LABEL / _BASE_URL / _API_KEY / _MODEL in .env.
PROVIDER_IDS: tuple[str, ...] = ("lmstudio", "zhipu", "deepseek")


class ProviderConfig(BaseModel):
    id: str
    label: str
    base_url: str
    api_key: str
    model: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    default_provider_id: str = "zhipu"
    max_agent_steps: int = 10

    # Provider 1: LM Studio (local)
    lmstudio_label: str = "本地 LM Studio"
    lmstudio_base_url: str = "http://127.0.0.1:1234/v1"
    lmstudio_api_key: str = "lm-studio"
    lmstudio_model: str = "zai-org/glm-4.7-flash"

    # Provider 2: Zhipu BigModel (cloud)
    zhipu_label: str = "智谱云 GLM-4.7-Flash"
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_api_key: str = ""
    zhipu_model: str = "glm-4.7-flash"

    # Provider 3: DeepSeek (cloud, paid but cheap; fast TTFT, strong tool use)
    deepseek_label: str = "DeepSeek V3"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"

    # Embedding — locked to one provider (see README)
    llm_embedding_base_url: str = "http://127.0.0.1:1234/v1"
    llm_embedding_api_key: str = "lm-studio"
    llm_embedding_model: str = "text-embedding-nomic-embed-text-v1.5"

    # RAG / Chroma
    chroma_db_path: str = "./data/chroma"
    chroma_collection_name: str = "finsight_cases"
    rag_cases_dir: str = "./backend/knowledge_base/cases"

    # Storage / misc
    db_path: str = "./data/finsight.db"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def providers(self) -> list[ProviderConfig]:
        result: list[ProviderConfig] = []
        for pid in PROVIDER_IDS:
            base_url = getattr(self, f"{pid}_base_url", "")
            api_key = getattr(self, f"{pid}_api_key", "")
            # Skip providers without credentials (e.g. zhipu key left blank
            # on a machine that only runs local LM Studio).
            if not base_url or not api_key:
                continue
            result.append(ProviderConfig(
                id=pid,
                label=getattr(self, f"{pid}_label", pid),
                base_url=base_url,
                api_key=api_key,
                model=getattr(self, f"{pid}_model", ""),
            ))
        return result

    def get_provider(self, provider_id: str | None) -> ProviderConfig:
        """Resolve a provider_id (or default) to its config. Raises KeyError
        when the id is unknown or lacks credentials."""
        resolved = provider_id or self.default_provider_id
        for p in self.providers:
            if p.id == resolved:
                return p
        raise KeyError(f"Unknown or unconfigured provider_id: {resolved}")


settings = Settings()
