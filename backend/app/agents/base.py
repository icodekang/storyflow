"""
pi-mono Agent 基类
所有 Pipeline Agent 继承此类，只需实现 4 个抽象方法
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.session import Session

import httpx


@dataclass
class AgentContext:
    """Agent 执行时的完整上下文"""
    session_id: str
    story_id: str
    input_data: dict
    memory_context: list[dict] = field(default_factory=list)
    human_feedback: str | None = None
    session: "Session | None" = None


class BaseAgent(ABC):
    """pi-mono Agent 基类"""

    name: str = "BaseAgent"
    description: str = ""

    def __init__(self, session: "Session"):
        self.session = session

    async def execute(self, context: AgentContext) -> dict:
        """
        统一执行流程：
        1. 检索记忆
        2. 构建 prompt
        3. 调用 LLM
        4. 解析输出
        5. 写入记忆
        6. 返回输出
        """
        # 1. 检索记忆
        query = self._get_search_query(context.input_data)
        memory_results = []
        if self.session.memory:
            memory_results = await self.session.memory.search(query, top_k=3)

        # 2. 构建 prompt
        prompt = self._build_prompt(context, memory_results)

        # 3. 调用 LLM
        raw_output = await self._call_llm(prompt, context.human_feedback)

        # 4. 解析输出
        parsed = self._parse_output(raw_output)

        # 5. 写入记忆
        if self.session.memory:
            await self.session.memory.add(self.name, parsed)

        return parsed

    @abstractmethod
    def _get_search_query(self, input_data: dict) -> str:
        """从输入数据中提取用于检索记忆的 query"""
        raise NotImplementedError

    @abstractmethod
    def _build_prompt(self, context: AgentContext, memory_results: list[dict]) -> str:
        """构建发送给 LLM 的完整 prompt"""
        raise NotImplementedError

    @abstractmethod
    async def _call_llm(self, prompt: str, human_feedback: str | None) -> str:
        """调用 LLM，返回原始文本输出"""
        raise NotImplementedError

    @abstractmethod
    def _parse_output(self, raw_output: str) -> dict:
        """解析 LLM 输出为结构化 dict"""
        raise NotImplementedError


class MockLLMMixin:
    """Mock LLM Mixin——用于骨架阶段返回预设数据"""

    async def _call_llm(self, prompt: str, human_feedback: str | None) -> str:
        return "{}"
