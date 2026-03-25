"""
pi-mono Session 管理器
负责每个 story 生成会话的生命周期管理
"""
import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

import aiofiles

from app.core.memory import MemoryLayer


class SessionStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"       # 等待人工干预
    DONE = "done"
    ERROR = "error"


class Session:
    """单次 story 生成会话"""

    def __init__(
        self,
        session_id: str | None = None,
        story_id: str = "",
        mode: Literal["auto", "human"] = "auto",
    ):
        self.session_id: str = session_id or str(uuid.uuid4())
        self.story_id: str = story_id
        self.created_at: datetime = datetime.now()
        self.status: SessionStatus = SessionStatus.RUNNING
        self.current_agent: Optional[str] = None
        self.mode: Literal["auto", "human"] = mode
        self.memory: MemoryLayer | None = None  # 初始化后由 SessionManager 注入

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "story_id": self.story_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "current_agent": self.current_agent,
            "mode": self.mode,
        }


class SessionManager:
    """
    全局 Session 管理器

    - 管理所有活跃 Session
    - 通过 Semaphore 控制最大并发数
    - 支持 Redis 持久化（Session 恢复）
    """

    def __init__(self, max_concurrent: int = 3):
        self._sessions: dict[str, Session] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, session_id: str) -> asyncio.Lock:
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        return self._locks[session_id]

    async def create_session(
        self,
        story_id: str,
        mode: Literal["auto", "human"] = "auto",
    ) -> Session:
        """创建新 Session 并初始化 MemoryLayer（立即返回，不占并发 slot）"""
        session = Session(story_id=story_id, mode=mode)
        session.memory = MemoryLayer(session)
        self._sessions[session.session_id] = session
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取已有 Session"""
        return self._sessions.get(session_id)

    async def get_session_by_story_id(self, story_id: str) -> Optional[Session]:
        """通过 story_id 查找 Session"""
        for session in self._sessions.values():
            if session.story_id == story_id:
                return session
        return None

    async def update_status(
        self,
        session_id: str,
        status: SessionStatus,
        current_agent: Optional[str] = None,
    ) -> None:
        """更新 Session 状态"""
        session = self._sessions.get(session_id)
        if session:
            session.status = status
            if current_agent is not None:
                session.current_agent = current_agent

    async def remove_session(self, session_id: str) -> None:
        """移除 Session"""
        self._sessions.pop(session_id, None)

    async def list_sessions(self) -> list[Session]:
        """列出所有活跃 Session"""
        return list(self._sessions.values())

    async def persist_session(self, session: Session) -> None:
        """将 Session 状态写入 JSON 文件（用于服务重启恢复）"""
        session_dir = "data/memory/sessions"
        import os
        os.makedirs(session_dir, exist_ok=True)
        path = f"{session_dir}/{session.session_id}.json"
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(session.to_dict(), ensure_ascii=False, indent=2))

    async def restore_session(self, session_id: str) -> Optional[Session]:
        """从 JSON 文件恢复 Session"""
        path = f"data/memory/sessions/{session_id}.json"
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
            session = Session(
                session_id=data["session_id"],
                story_id=data["story_id"],
                mode=data.get("mode", "auto"),
            )
            session.status = SessionStatus(data["status"])
            session.current_agent = data.get("current_agent")
            from datetime import datetime
            session.created_at = datetime.fromisoformat(data["created_at"])
            session.memory = MemoryLayer(session)
            self._sessions[session_id] = session
            return session
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            return None

    @property
    def semaphore(self) -> asyncio.Semaphore:
        return self._semaphore


# 全局单例
session_manager = SessionManager()
