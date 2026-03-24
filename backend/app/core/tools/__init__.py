"""
pi-mono 工具注册表
所有 Agent 共享的统一工具集
"""
from typing import Any, Callable


class ToolRegistry:
    """统一工具注册表"""

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, func: Callable) -> None:
        self._tools[name] = func

    def get(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def call(self, name: str, **kwargs) -> Any:
        tool = self.get(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")
        return tool(**kwargs)


# 全局单例
tools = ToolRegistry()


# ─── 默认工具占位（骨架阶段）────────────────────────────────


async def memory_search_tool(query: str, top_k: int = 3) -> list[dict]:
    """记忆检索工具"""
    return []


async def llm_call_tool(prompt: str, model: str = "gpt-4o") -> str:
    """LLM 调用工具"""
    return "{}"


async def video_generate_tool(scene_description: str, output_path: str) -> dict:
    """视频生成工具"""
    return {"status": "mock", "path": output_path}


async def storage_save_tool(content: bytes, path: str) -> dict:
    """存储保存工具"""
    return {"status": "mock", "path": path}


# 注册默认工具
tools.register("memory_search", memory_search_tool)
tools.register("llm_call", llm_call_tool)
tools.register("video_generate", video_generate_tool)
tools.register("storage_save", storage_save_tool)
