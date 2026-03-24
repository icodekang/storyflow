"""
Agent 3: ScenePlanning（分镜规划）
"""
from datetime import datetime

from app.agents.base import AgentContext, BaseAgent


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
            {
                "scene_id": "sc_03",
                "scene_number": 3,
                "act": 2,
                "description": "主角走出家门，迈向未知",
                "location": "室外",
                "time_of_day": "morning",
                "weather": "晴",
                "emotion": "坚定",
                "camera_angle": "wide",
                "transition": "fade",
                "duration_sec": 15,
            },
        ],
        "total_scenes": 3,
        "estimated_total_duration": 30,
    },
}


class ScenePlanningAgent(BaseAgent):
    name = "ScenePlanning"
    description = "规划视频分镜，输出场景列表"

    def _get_search_query(self, input_data: dict) -> str:
        acts = input_data.get("act_structure", {})
        return str(acts)

    def _build_prompt(self, context: AgentContext, memory_results: list[dict]) -> str:
        return f"根据以下结构规划分镜：\n{context.input_data}"

    async def _call_llm(self, prompt: str, human_feedback: str | None) -> str:
        return "{}"

    def _parse_output(self, raw_output: str) -> dict:
        return MOCK_OUTPUT
