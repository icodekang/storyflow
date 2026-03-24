"""
Pipeline Orchestrator — 多 Agent 协作编排器
"""
from typing import Literal

from app.core.session import Session, SessionStatus, session_manager
from app.agents.base import AgentContext


class PipelineOrchestrator:
    """多 Agent 协作编排器"""

    def __init__(self, session: Session, mode: Literal["auto", "human"]):
        self.session = session
        self.mode = mode
        self._agents: list[type] = []

    def register_agents(self, agents: list[type]) -> None:
        self._agents = agents

    async def run(self, story_id: str, initial_input: dict, ws=None) -> dict:
        """
        执行完整 pipeline

        Args:
            story_id: story 标识
            initial_input: 初始输入（如 story_text）
            ws: WebSocket 连接（可选，用于实时推送）

        Returns:
            最终输出
        """
        self.session.status = SessionStatus.RUNNING
        current_input = initial_input

        for agent_cls in self._agents:
            agent = agent_cls(session=self.session)
            self.session.current_agent = agent.name

            # 推送 Agent 开始状态
            if ws:
                await ws.send_json({
                    "type": "agent_status",
                    "agent": agent.name,
                    "status": "running",
                })

            # 构建上下文
            context = AgentContext(
                session_id=self.session.session_id,
                story_id=story_id,
                input_data=current_input,
                memory_context=[],
                session=self.session,
            )

            # 执行 Agent
            output = await agent.execute(context)

            # 推送 Agent 输出
            if ws:
                await ws.send_json({
                    "type": "agent_output",
                    "agent": agent.name,
                    "output": output,
                })

            # 人工干预模式
            if self.mode == "human" and ws:
                self.session.status = SessionStatus.PAUSED
                await ws.send_json({
                    "type": "agent_waiting",
                    "agent": agent.name,
                    "output": output,
                })
                # 骨架阶段：跳过实际等待，直接继续
                # 实际实现通过 Redis PubSub 等待前端干预指令
                self.session.status = SessionStatus.RUNNING

            current_input = output

        self.session.status = SessionStatus.DONE
        if ws:
            await ws.send_json({"type": "story_complete", "final_output": current_input})

        return current_input
