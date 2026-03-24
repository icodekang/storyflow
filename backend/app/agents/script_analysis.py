"""
Agent 1: ScriptAnalysis（剧本分析）
"""
from datetime import datetime

from app.agents.base import AgentContext, BaseAgent, MockLLMMixin
from app.services.llm import LLMConfig


MOCK_OUTPUT = {
    "agent_name": "ScriptAnalysis",
    "timestamp": datetime.now().isoformat(),
    "data": {
        "story_summary": "一个关于成长与救赎的故事。",
        "genre": "剧情",
        "sub_genre": "现实主义",
        "tone": "温暖而略带忧伤",
        "target_audience": "18-35岁",
        "themes": ["成长", "救赎", "人性", "希望"],
        "mood_tags": ["温情", "感人", "治愈"],
        "estimated_duration_sec": 180,
        "language": "zh-CN",
    },
}


class ScriptAnalysisAgent(MockLLMMixin, BaseAgent):
    name = "ScriptAnalysis"
    description = "分析输入剧本，输出题材、基调、主题等元数据"
    llm_config = LLMConfig(provider="openai", model="gpt-4o")

    def _get_search_query(self, input_data: dict) -> str:
        return input_data.get("story_text", "")

    def _build_prompt(self, context: AgentContext, memory_results: list[dict]) -> str:
        story = context.input_data.get("story_text", "")
        return f"分析以下故事文本，输出题材、基调、主题等：\n{story[:500]}"

    def _parse_output(self, raw_output: str) -> dict:
        return MOCK_OUTPUT
