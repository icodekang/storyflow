"""
StoryFlow FastAPI 入口
"""
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.session import session_manager, SessionStatus
from app.models import (
    StoryCreate,
    StoryResponse,
    AgentOutputResponse,
    InterventionRequest,
)
from app.api.websocket import websocket_handler, manager


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── 健康检查 ────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


# ─── Stories API ─────────────────────────────────────────


@app.post("/api/stories", response_model=StoryResponse)
async def create_story(body: StoryCreate):
    """创建新 story 并返回 session_id"""
    session = await session_manager.create_session(
        story_id=body.title or body.story_text[:50],
        mode=body.mode,
    )
    return StoryResponse(
        story_id=session.story_id,
        session_id=session.session_id,
        status=session.status.value,
        mode=session.mode,
    )


@app.get("/api/stories/{story_id}")
async def get_story(story_id: str):
    """获取 story 状态"""
    session = await session_manager.get_session_by_story_id(story_id)
    if not session:
        return {"error": "not_found"}, 404
    return {
        "story_id": session.story_id,
        "session_id": session.session_id,
        "status": session.status.value,
        "current_agent": session.current_agent,
        "mode": session.mode,
    }


@app.get("/api/stories/{story_id}/agents")
async def get_story_agents(story_id: str):
    """获取 story 各 agent 输出状态"""
    session = await session_manager.get_session_by_story_id(story_id)
    if not session:
        return {"error": "not_found"}, 404
    history = []
    if session.memory:
        history = await session.memory.get_context_for_agent(None)
    return {"agents": history}


@app.get("/api/queue")
async def get_queue_status():
    """获取当前任务队列状态"""
    from app.core.scheduler import scheduler
    return await scheduler.get_queue_status()


@app.post("/api/stories/{story_id}/generate")
async def start_story_generation(story_id: str, body: StoryCreate):
    """触发 story 生成 pipeline（异步，后台运行）"""
    session = await session_manager.get_session_by_story_id(story_id)
    if not session:
        # 自动创建 session
        session = await session_manager.create_session(story_id=story_id, mode=body.mode)

    # 通过 Scheduler 提交任务（已通过 WebSocket submit，这里仅作 HTTP 兼容）
    return {"status": "queued", "story_id": story_id, "session_id": session.session_id}

    return {"status": "started", "story_id": story_id, "session_id": session.session_id}


# ─── Agent API ───────────────────────────────────────────


@app.post("/api/agents/{story_id}/{agent_name}/intervene")
async def intervene(story_id: str, agent_name: str, body: InterventionRequest):
    """人工干预接口——写入 Redis，由 WebSocket handler 读取"""
    try:
        import redis.asyncio as redis
        import json as _json
        from app.core.config import settings as _settings
        r = redis.from_url(_settings.redis_url)
        key = f"intervention:{story_id}:{agent_name}"
        await r.set(key, _json.dumps({"action": body.action, "feedback": body.feedback or ""}), ex=3600)
        await r.aclose()
    except Exception:
        pass  # Redis 不可用时跳过
    return {"status": "ok", "action": body.action}


@app.get("/api/agents/{story_id}/{agent_name}/output", response_model=AgentOutputResponse)
async def get_agent_output(story_id: str, agent_name: str):
    """获取某个 Agent 的输出"""
    session = await session_manager.get_session_by_story_id(story_id)
    if not session:
        return AgentOutputResponse(agent=agent_name, output={})
    if session.memory:
        history = await session.memory.get_context_for_agent(agent_name)
        entries = [h for h in history if h.get("agent") == agent_name]
        if entries:
            return AgentOutputResponse(agent=agent_name, output=entries[-1].get("output", {}))
    return AgentOutputResponse(agent=agent_name, output={})


# ─── WebSocket ────────────────────────────────────────────


@app.websocket("/ws/stories/{story_id}")
async def story_websocket(ws: WebSocket, story_id: str):
    """WebSocket 实时推送 story 生成进度"""
    await websocket_handler(ws, story_id)


# ─── 静态文件（骨架阶段预览）───────────────────────────────


@app.get("/storage/{path:path}")
async def serve_storage(path: str):
    """本地存储文件访问"""
    from pathlib import Path
    file_path = Path(settings.STORAGE_LOCAL_ROOT) / path
    if not file_path.exists():
        return {"error": "not_found"}, 404
    return FileResponse(file_path)


# ─── 启动时恢复 session ───────────────────────────────────


@app.on_event("startup")
async def startup():
    # 启动 Pipeline 调度器（启动 worker pool）
    from app.core.scheduler import scheduler
    scheduler.start()
    # TODO: 从 Redis 恢复未完成的 session
