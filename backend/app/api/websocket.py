"""
WebSocket 实时通信
"""
import asyncio
import json
from typing import Literal

from fastapi import WebSocket, WebSocketDisconnect

from app.core.session import Session, session_manager, SessionStatus
from app.core.orchestrator import PipelineOrchestrator
from app.agents import PIPELINE_AGENTS


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, story_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[story_id] = ws

    def disconnect(self, story_id: str) -> None:
        self._connections.pop(story_id, None)

    async def send_json(self, story_id: str, data: dict) -> bool:
        ws = self._connections.get(story_id)
        if ws is None:
            return False
        try:
            await ws.send_json(data)
            return True
        except Exception:
            self.disconnect(story_id)
            return False

    def get_ws(self, story_id: str) -> WebSocket | None:
        return self._connections.get(story_id)


manager = ConnectionManager()


async def run_pipeline(story_id: str, story_text: str, mode: Literal["auto", "human"] = "auto") -> None:
    """后台运行 pipeline，通过 WebSocket 推送进度"""
    # 创建 session
    session = await session_manager.create_session(story_id=story_id, mode=mode)
    ws = manager.get_ws(story_id)

    # 构建 orchestrator
    orchestrator = PipelineOrchestrator(session=session, mode=mode)
    orchestrator.register_agents(PIPELINE_AGENTS)

    try:
        initial_input = {"story_text": story_text}
        await orchestrator.run(story_id, initial_input, ws=ws)
    except Exception as e:
        await session_manager.update_status(session.session_id, SessionStatus.ERROR)
        await manager.send_json(story_id, {
            "type": "story_error",
            "error": str(e),
        })
    finally:
        manager.disconnect(story_id)


async def websocket_handler(ws: WebSocket, story_id: str) -> None:
    """处理 WebSocket 连接"""
    await manager.connect(story_id, ws)

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await ws.send_json({"type": "pong"})
            elif msg_type == "start":
                # 前端触发 story 生成（后台运行）
                story_text = data.get("story_text", "")
                mode = data.get("mode", "auto")
                asyncio.create_task(run_pipeline(story_id, story_text, mode))
                await ws.send_json({"type": "started", "story_id": story_id})
            elif msg_type == "intervene":
                # 前端干预指令
                agent_name = data.get("agent_name", "")
                action = data.get("action", "confirm")
                feedback = data.get("feedback", "")
                # 写入 Redis，后续 orchestrator 读取
                await _publish_intervention(story_id, agent_name, action, feedback)
                await ws.send_json({"type": "intervention_received"})
            elif msg_type == "fetch_session":
                # 前端拉取当前 session 状态
                session = await session_manager.get_session_by_story_id(story_id)
                if session:
                    await ws.send_json({
                        "type": "session_state",
                        "story_id": story_id,
                        "status": session.status.value,
                        "current_agent": session.current_agent,
                    })

    except WebSocketDisconnect:
        manager.disconnect(story_id)


async def _publish_intervention(story_id: str, agent_name: str, action: str, feedback: str) -> None:
    """发布干预指令到 Redis"""
    try:
        import redis.asyncio as redis
        from app.core.config import settings
        r = redis.from_url(settings.redis_url)
        key = f"intervention:{story_id}:{agent_name}"
        import json
        await r.set(key, json.dumps({"action": action, "feedback": feedback}), ex=3600)
        await r.aclose()
    except Exception:
        # Redis 不可用时跳过（骨架阶段不影响）
        pass
