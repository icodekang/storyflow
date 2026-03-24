"""
Agent 7: QCReview（质检复审）
"""
from datetime import datetime

from app.agents.base import AgentContext, BaseAgent, MockLLMMixin
from app.services.llm import LLMConfig


MOCK_OUTPUT = {
    "agent_name": "QCReview",
    "timestamp": datetime.now().isoformat(),
    "data": {
        "quality_score": 75,
        "issues": [
            {
                "severity": "minor",
                "type": "consistency",
                "description": "角色服装在两场景间略有差异",
                "affected_scene_id": "sc_02",
                "suggestion": "统一服装设定",
            }
        ],
        "recommendations": [
            "适当增加背景音乐丰富情感",
            "部分转场可更加流畅",
        ],
        "passed": True,
    },
}


class QCReviewAgent(MockLLMMixin, BaseAgent):
    name = "QCReview"
    description = "对生成的视频进行质量检查与评分"
    # 质检用 Claude（更严格的审查能力）
    llm_config = LLMConfig(provider="anthropic", model="claude-3-5-sonnet-20241022")

    def _get_search_query(self, input_data: dict) -> str:
        return input_data.get("final_video_path", "")

    def _build_prompt(self, context: AgentContext, memory_results: list[dict]) -> str:
        return f"质检以下视频：\n{context.input_data}"

    def _parse_output(self, raw_output: str) -> dict:
        return MOCK_OUTPUT
