"""
LLM Service — 统一 LLM 调用层
支持 OpenAI / Anthropic，可按 Agent 独立配置模型
"""
import json
import os
from dataclasses import dataclass, field
from typing import Literal

import httpx

from app.core.config import settings


@dataclass
class LLMConfig:
    """单个 Agent 的 LLM 配置"""
    provider: Literal["openai", "anthropic"] = "openai"
    model: str = "gpt-4o"
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048

    @property
    def effective_api_key(self) -> str | None:
        return self.api_key or (
            settings.OPENAI_API_KEY if self.provider == "openai"
            else settings.ANTHROPIC_API_KEY
        )

    @property
    def effective_model(self) -> str:
        return self.model or (
            settings.OPENAI_MODEL if self.provider == "openai"
            else settings.ANTHROPIC_MODEL
        )


def _load_agent_llm_config() -> dict[str, LLMConfig]:
    """从环境变量加载每个 Agent 的 LLM 配置"""
    # 格式: LLM_AGENT_ScriptAnalysis={"provider":"openai","model":"gpt-4o"}
    configs: dict[str, LLMConfig] = {}
    prefix = "LLM_AGENT_"
    for key, val in os.environ.items():
        if key.startswith(prefix):
            agent_name = key[len(prefix):]
            try:
                data = json.loads(val)
                configs[agent_name] = LLMConfig(**data)
            except (json.JSONDecodeError, TypeError):
                pass
    return configs


# 全局 Agent 配置缓存
_agent_llm_configs: dict[str, LLMConfig] | None = None


def get_agent_llm_config(agent_name: str, agent_cls=None) -> LLMConfig:
    """
    获取指定 Agent 的 LLM 配置
    优先级：环境变量 > Agent 类属性 llm_config > 全局默认
    """
    global _agent_llm_configs
    if _agent_llm_configs is None:
        _agent_llm_configs = _load_agent_llm_config()

    # 1. 优先环境变量覆盖
    if agent_name in _agent_llm_configs:
        return _agent_llm_configs[agent_name]

    # 2. 查 Agent 类属性
    if agent_cls is not None:
        cls_attr = getattr(agent_cls, "llm_config", None)
        if isinstance(cls_attr, LLMConfig):
            return cls_attr

    # 3. 全局默认
    return LLMConfig(
        provider=settings.LLM_PROVIDER,
        model=settings.OPENAI_MODEL if settings.LLM_PROVIDER == "openai" else settings.ANTHROPIC_MODEL,
    )


class LLMService:
    """
    LLM 调用服务

    用法:
        service = LLMService()
        result = await service.call(prompt, config=LLMConfig(provider="openai", model="gpt-4o"))
    """

    def __init__(self):
        self._openai_client: httpx.AsyncClient | None = None
        self._anthropic_client: httpx.AsyncClient | None = None

    def _get_openai_client(self) -> httpx.AsyncClient:
        if self._openai_client is None:
            self._openai_client = httpx.AsyncClient(
                base_url="https://api.openai.com/v1",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                timeout=60.0,
            )
        return self._openai_client

    def _get_anthropic_client(self) -> httpx.AsyncClient:
        if self._anthropic_client is None:
            self._anthropic_client = httpx.AsyncClient(
                base_url="https://api.anthropic.com/v1",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY or "",
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._anthropic_client

    async def call(
        self,
        prompt: str,
        config: LLMConfig | None = None,
        human_feedback: str | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """
        调用 LLM，返回原始文本

        Args:
            prompt: 用户 prompt
            config: LLM 配置（None 使用全局默认）
            human_feedback: 人工反馈，非空则追加到 prompt
            system_prompt: 系统提示词
        """
        if config is None:
            config = LLMConfig()

        full_prompt = prompt
        if human_feedback:
            full_prompt += f"\n\n【人工修改建议】：{human_feedback}\n请根据此建议重新生成输出。"

        if config.provider == "openai":
            return await self._call_openai(full_prompt, config, system_prompt)
        elif config.provider == "anthropic":
            return await self._call_anthropic(full_prompt, config, system_prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {config.provider}")

    async def _call_openai(
        self,
        prompt: str,
        config: LLMConfig,
        system_prompt: str | None,
    ) -> str:
        """调用 OpenAI Chat Completions API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        api_key = config.effective_api_key or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )
        try:
            response = await client.post(
                "/chat/completions",
                json={
                    "model": config.effective_model,
                    "messages": messages,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        finally:
            await client.aclose()

    async def _call_anthropic(
        self,
        prompt: str,
        config: LLMConfig,
        system_prompt: str | None,
    ) -> str:
        """调用 Anthropic Messages API"""
        api_key = config.effective_api_key or settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("Anthropic API key not configured")

        client = httpx.AsyncClient(
            base_url="https://api.anthropic.com/v1",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        try:
            body: dict = {
                "model": config.effective_model,
                "max_tokens": config.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                body["system"] = system_prompt

            response = await client.post("/messages", json=body)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        finally:
            await client.aclose()


# 全局单例
llm_service = LLMService()
