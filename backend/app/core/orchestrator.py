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
                # 人工干预：等待 Redis 中的干预指令（最多30分钟）
                intervention = await self._wait_for_intervention(story_id, agent.name)
                if intervention["action"] == "regenerate":
                    context.human_feedback = intervention.get("feedback", "")
                    output = await agent.execute(context)
                elif intervention["action"] == "skip":
                    output = {}
                # confirm 什么都不做，直接继续
                self.session.status = SessionStatus.RUNNING

            current_input = output

        self.session.status = SessionStatus.DONE
        if ws:
            await ws.send_json({"type": "story_complete", "final_output": current_input})

        return current_input

    async def _wait_for_intervention(self, story_id: str, agent_name: str) -> dict:
        """阻塞等待前端干预指令（Redis GET + 超时轮询）"""
        import asyncio
        key = f"intervention:{story_id}:{agent_name}"
        try:
            import redis.asyncio as redis
            import json
            from app.core.config import settings
            r = redis.from_url(settings.redis_url)
            timeout = settings.INTERVENTION_TIMEOUT_SEC
            interval = 2
            elapsed = 0
            while elapsed < timeout:
                val = await r.get(key)
                if val:
                    await r.delete(key)
                    await r.aclose()
                    return json.loads(val)
                await asyncio.sleep(interval)
                elapsed += interval
            await r.aclose()
        except Exception:
            pass
        return {"action": "confirm", "feedback": ""}
