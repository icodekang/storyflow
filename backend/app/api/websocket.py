"""
WebSocket 实时通信
"""
import asyncio
import json
from typing import Literal

from fastapi import WebSocket, WebSocketDisconnect

from app.core.session import Session, session_manager, SessionStatus
from app.core.scheduler import scheduler


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


async def ws_send_wrapper(story_id: str, data: dict) -> None:
    """WebSocket 推送的异步包装"""
    await manager.send_json(story_id, data)


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
                # 提交任务到调度器（排队等执行）
                story_text = data.get("story_text", "")
                mode = data.get("mode", "auto")
                agent_llm_config = data.get("agent_llm_config")

                job_id = await scheduler.submit(
                    story_id=story_id,
                    mode=mode,
                    initial_input={"story_text": story_text},
                    agent_llm_config=agent_llm_config,
                    ws_send=lambda d: ws_send_wrapper(story_id, d),
                )

                await ws.send_json({"type": "started", "story_id": story_id, "job_id": job_id})

            elif msg_type == "intervene":
                # 前端干预指令
                agent_name = data.get("agent_name", "")
                action = data.get("action", "confirm")
                feedback = data.get("feedback", "")
                await _publish_intervention(story_id, agent_name, action, feedback)
                await ws.send_json({"type": "intervention_received"})

            elif msg_type == "fetch_session":
                session = await session_manager.get_session_by_story_id(story_id)
                if session:
                    await ws.send_json({
                        "type": "session_state",
                        "story_id": story_id,
                        "status": session.status.value,
                        "current_agent": session.current_agent,
                    })

            elif msg_type == "cancel":
                await scheduler.cancel_job(story_id)
                await ws.send_json({"type": "cancelled", "story_id": story_id})

            elif msg_type == "queue_status":
                status = await scheduler.get_queue_status()
                await ws.send_json({"type": "queue_status", **status})

    except WebSocketDisconnect:
        manager.disconnect(story_id)


async def _publish_intervention(story_id: str, agent_name: str, action: str, feedback: str) -> None:
    """发布干预指令到 Redis"""
    try:
        import redis.asyncio as redis
        from app.core.config import settings
        r = redis.from_url(settings.redis_url)
        key = f"intervention:{story_id}:{agent_name}"
        await r.set(key, json.dumps({"action": action, "feedback": feedback}), ex=3600)
        await r.aclose()
    except Exception:
        pass
