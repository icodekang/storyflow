"""
Agent 6: VideoAssembly（视频剪辑合成）
"""
from datetime import datetime

from app.agents.base import AgentContext, BaseAgent


MOCK_OUTPUT = {
    "agent_name": "VideoAssembly",
    "timestamp": datetime.now().isoformat(),
    "data": {
        "final_video_path": "data/storage/output.mp4",
        "final_video_url": "",
        "duration_sec": 30,
        "resolution": "1920x1080",
        "codec": "h.264",
        "fps": 24,
        "assembly_edl": "Mock EDL content",
        "scenes_in_order": ["sc_01", "sc_02", "sc_03"],
        "file_size_mb": 0,
    },
}


class VideoAssemblyAgent(BaseAgent):
    name = "VideoAssembly"
    description = "将视觉素材拼接为完整视频"

    def _get_search_query(self, input_data: dict) -> str:
        assets = input_data.get("visual_assets", [])
        return str(assets[0]) if assets else ""

    def _build_prompt(self, context: AgentContext, memory_results: list[dict]) -> str:
        return f"组装以下素材为视频：\n{context.input_data}"

    async def _call_llm(self, prompt: str, human_feedback: str | None) -> str:
        return "{}"

    def _parse_output(self, raw_output: str) -> dict:
        return MOCK_OUTPUT
