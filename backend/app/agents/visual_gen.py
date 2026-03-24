"""
Agent 5: VisualGen（视觉生成）
"""
from datetime import datetime

from app.agents.base import AgentContext, BaseAgent


MOCK_OUTPUT = {
    "agent_name": "VisualGen",
    "timestamp": datetime.now().isoformat(),
    "data": {
        "visual_assets": [
            {
                "asset_id": "asset_01",
                "scene_id": "sc_01",
                "character_id": "char_01",
                "asset_type": "image",
                "prompt": "A young person sitting by the window on a rainy night, melancholic atmosphere, cinematic lighting",
                "negative_prompt": "cartoon, anime, low quality",
                "generation_params": {"model": "sdxl", "resolution": "1024x1024", "seed": 42},
                "output_path": "data/storage/asset_01.png",
                "output_url": "",
                "status": "pending",
            },
            {
                "asset_id": "asset_02",
                "scene_id": "sc_02",
                "character_id": None,
                "asset_type": "image",
                "prompt": "A mysterious letter sliding under a door, rainy night background, dramatic lighting",
                "negative_prompt": "cartoon, anime, low quality",
                "generation_params": {"model": "sdxl", "resolution": "1024x1024", "seed": 43},
                "output_path": "data/storage/asset_02.png",
                "output_url": "",
                "status": "pending",
            },
        ]
    },
}


class VisualGenAgent(BaseAgent):
    name = "VisualGen"
    description = "生成视觉素材（图像/视频片段）"

    def _get_search_query(self, input_data: dict) -> str:
        scenes = input_data.get("scenes", [])
        return str(scenes[0]) if scenes else ""

    def _build_prompt(self, context: AgentContext, memory_results: list[dict]) -> str:
        return f"为以下场景生成视觉素材：\n{context.input_data}"

    async def _call_llm(self, prompt: str, human_feedback: str | None) -> str:
        return "{}"

    def _parse_output(self, raw_output: str) -> dict:
        return MOCK_OUTPUT
