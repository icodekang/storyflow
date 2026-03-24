"""
Agent 5: VisualGen（视觉生成）
"""
from datetime import datetime

from app.agents.base import AgentContext, BaseAgent, MockLLMMixin
from app.services.llm import LLMConfig


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
        ]
    },
}


class VisualGenAgent(MockLLMMixin, BaseAgent):
    name = "VisualGen"
    description = "生成视觉素材（图像/视频片段）"
    # 视觉生成用 GPT-4o（理解场景描述生成精准 prompt）
    llm_config = LLMConfig(provider="openai", model="gpt-4o")

    def _get_search_query(self, input_data: dict) -> str:
        scenes = input_data.get("scenes", [])
        return str(scenes[0]) if scenes else ""

    def _build_prompt(self, context: AgentContext, memory_results: list[dict]) -> str:
        return f"为以下场景生成视觉素材：\n{context.input_data}"

    def _parse_output(self, raw_output: str) -> dict:
        return MOCK_OUTPUT
