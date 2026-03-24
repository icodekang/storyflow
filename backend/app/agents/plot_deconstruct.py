"""
Agent 2: PlotDeconstruct（情节拆解）
"""
from datetime import datetime

from app.agents.base import AgentContext, BaseAgent, MockLLMMixin
from app.services.llm import LLMConfig


MOCK_OUTPUT = {
    "agent_name": "PlotDeconstruct",
    "timestamp": datetime.now().isoformat(),
    "data": {
        "act_structure": {
            "act1": {
                "title": "序幕",
                "description": "主角陷入人生低谷",
                "ending_hook": "一封神秘来信打破平静",
            },
            "act2": {
                "title": "冲突与探索",
                "description": "主角踏上寻找真相的旅程",
                "rising_action": ["遇见导师", "遭遇挫折", "内心挣扎"],
                "midpoint_twist": "真正的敌人是曾经的自己",
            },
            "act3": {
                "title": "高潮与结局",
                "description": "最终对决与自我和解",
                "climax": "与过去和解的感人场景",
                "resolution": "带着新的希望继续前行",
            },
        },
        "key_plot_points": [
            {"point_id": 1, "type": "inciting_incident", "description": "收到神秘来信", "emotion": "困惑"},
            {"point_id": 2, "type": "rising_action", "description": "踏上旅程", "emotion": "期待"},
            {"point_id": 3, "type": "climax", "description": "自我对峙", "emotion": "震撼"},
        ],
        "conflict": "内心的恐惧与外在的困境交织",
        "pacing": "中等节奏，张弛有度",
    },
}


class PlotDeconstructAgent(MockLLMMixin, BaseAgent):
    name = "PlotDeconstruct"
    description = "将剧本拆解为三幕结构与关键情节点"
    llm_config = LLMConfig(provider="openai", model="gpt-4o")

    def _get_search_query(self, input_data: dict) -> str:
        return input_data.get("story_summary", "")

    def _build_prompt(self, context: AgentContext, memory_results: list[dict]) -> str:
        summary = context.input_data.get("story_summary", "")
        return f"将以下故事拆解为三幕结构：\n{summary}"

    def _parse_output(self, raw_output: str) -> dict:
        return MOCK_OUTPUT
