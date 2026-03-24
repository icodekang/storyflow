"""
Agent 3: ScenePlanning（分镜规划）
"""
from datetime import datetime

from app.agents.base import AgentContext, BaseAgent, MockLLMMixin
from app.services.llm import LLMConfig


MOCK_OUTPUT = {
    "agent_name": "ScenePlanning",
    "timestamp": datetime.now().isoformat(),
    "data": {
        "scenes": [
            {
                "scene_id": "sc_01",
                "scene_number": 1,
                "act": 1,
                "description": "昏暗的房间，主角独自坐在窗边",
                "location": "室内",
                "time_of_day": "night",
                "weather": "雨",
                "emotion": "忧郁",
                "camera_angle": "medium",
                "transition": "cut",
                "duration_sec": 10,
            },
            {
                "scene_id": "sc_02",
                "scene_number": 2,
                "act": 1,
                "description": "一封信从门缝滑入",
                "location": "室内",
                "time_of_day": "night",
                "weather": "雨",
                "emotion": "好奇",
                "camera_angle": "close-up",
                "transition": "dissolve",
                "duration_sec": 5,
            },
        ],
        "total_scenes": 2,
        "estimated_total_duration": 15,
    },
}


class ScenePlanningAgent(MockLLMMixin, BaseAgent):
    name = "ScenePlanning"
    description = "规划视频分镜，输出场景列表"
    # 分镜规划任务相对简单，用 GPT-4o-mini 节省成本
    llm_config = LLMConfig(provider="openai", model="gpt-4o-mini")

    def _get_search_query(self, input_data: dict) -> str:
        acts = input_data.get("act_structure", {})
        return str(acts)

    def _build_prompt(self, context: AgentContext, memory_results: list[dict]) -> str:
        return f"根据以下结构规划分镜：\n{context.input_data}"

    def _parse_output(self, raw_output: str) -> dict:
        return MOCK_OUTPUT
