"""
StoryFlow 配置管理
所有环境变量统一入口
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "StoryFlow"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # ── Server ──────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── CORS ────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # ── Redis ───────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ── ChromaDB ────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "data/chroma"
    CHROMA_COLLECTION: str = "storyflow_memory"

    # ── LLM ─────────────────────────────────────────────
    # 全局默认（单个 Agent 未配置时使用）
    LLM_PROVIDER: str = "openai"  # openai | anthropic
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # ── Per-Agent LLM 配置 ──────────────────────────────
    # 通过环境变量注入，格式：LLM_AGENT_{AgentName}='{"provider":"openai","model":"gpt-4o-mini"}'
    # Agent 名称区分大小写，必须与 PIPELINE_AGENTS 中的类名一致
    # 示例：LLM_AGENT_ScriptAnalysis='{"provider":"openai","model":"gpt-4o"}'
    #       LLM_AGENT_QCReview='{"provider":"anthropic","model":"claude-3-5-sonnet-20241022"}'

    # ── Video / Storage ─────────────────────────────────
    VIDEO_GENERATOR_MODE: str = "ffmpeg"  # ffmpeg | runway | pika
    STORAGE_MODE: str = "local"  # local | oss
    STORAGE_LOCAL_ROOT: str = "data/storage"
    RUNWAY_API_KEY: str | None = None

    # ── Session ─────────────────────────────────────────
    SESSION_MAX_CONCURRENT: int = 3
    SESSION_DATA_DIR: str = "data/memory/sessions"

    # ── Intervention ─────────────────────────────────────
    INTERVENTION_TIMEOUT_SEC: int = 1800  # 30 min


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
