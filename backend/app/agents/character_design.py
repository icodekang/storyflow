"""
Agent 4: CharacterDesign（角色设计）
"""
from datetime import datetime

from app.agents.base import AgentContext, BaseAgent, MockLLMMixin
from app.services.llm import LLMConfig


MOCK_OUTPUT = {
    "agent_name": "CharacterDesign",
    "timestamp": datetime.now().isoformat(),
    "data": {
        "characters": [
            {
                "character_id": "char_01",
                "name": "主角",
                "role": "protagonist",
                "age_appearance": "二十多岁",
                "appearance": {
                    "face": "清秀，眼神坚毅",
                    "body": "中等身材",
                    "clothing": "简约日常装",
                    "distinctive_features": ["手腕上的旧伤疤"],
                },
                "personality": "内敛但内心强大",
                "backstory": "曾经历重大挫折",
                "motivation": "寻找真相，完成自我救赎",
                "voice_description": "低沉而有力",
                "relationships": [],
                "visual_keywords": ["年轻人", "简约服装", "雨天", "忧郁眼神"],
            }
        ],
        "narrator": {
            "voice_description": "温柔沉稳的女声",
            "tone": "叙述感强，不喧宾夺主",
        },
    },
}


class CharacterDesignAgent(MockLLMMixin, BaseAgent):
    name = "CharacterDesign"
    description = "设计角色外观、性格与关系"
    llm_config = LLMConfig(provider="openai", model="gpt-4o")

    def _get_search_query(self, input_data: dict) -> str:
        return input_data.get("story_text", "")

    def _build_prompt(self, context: AgentContext, memory_results: list[dict]) -> str:
        return f"根据以下内容设计角色：\n{context.input_data}"

    def _parse_output(self, raw_output: str) -> dict:
        return MOCK_OUTPUT
