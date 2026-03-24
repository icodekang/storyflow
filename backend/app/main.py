"""
StoryFlow FastAPI 入口
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.session import session_manager, SessionStatus
from app.models import (
    StoryCreate,
    StoryResponse,
    AgentOutputResponse,
    InterventionRequest,
)


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
    """创建新 story 并启动生成 session"""
    session = await session_manager.create_session(
        story_id=body.story_text[:50],  # 临时用文本前50字做id
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
    # 遍历查找（生产环境应优化索引）
    for s in await session_manager.list_sessions():
        if s.story_id == story_id:
            return {
                "story_id": s.story_id,
                "session_id": s.session_id,
                "status": s.status.value,
                "current_agent": s.current_agent,
                "mode": s.mode,
            }
    return {"error": "not_found"}, 404


@app.get("/api/stories/{story_id}/agents")
async def get_story_agents(story_id: str):
    """获取 story 各 agent 输出状态"""
    for s in await session_manager.list_sessions():
        if s.story_id == story_id:
            history = []
            if s.memory:
                history = await s.memory.get_context_for_agent(None)
            return {"agents": history}
    return {"error": "not_found"}, 404


# ─── Agent API ───────────────────────────────────────────


@app.post("/api/agents/{story_id}/{agent_name}/intervene")
async def intervene(story_id: str, agent_name: str, body: InterventionRequest):
    """人工干预接口"""
    # 骨架阶段：直接返回 success
    return {"status": "ok", "action": body.action}


@app.get("/api/agents/{story_id}/{agent_name}/output", response_model=AgentOutputResponse)
async def get_agent_output(story_id: str, agent_name: str):
    """获取某个 Agent 的输出"""
    for s in await session_manager.list_sessions():
        if s.story_id == story_id:
            if s.memory:
                history = await s.memory.get_context_for_agent(agent_name)
                entries = [h for h in history if h.get("agent") == agent_name]
                if entries:
                    return AgentOutputResponse(agent=agent_name, output=entries[-1].get("output", {}))
            return AgentOutputResponse(agent=agent_name, output={})
    return {"error": "not_found"}, 404


# ─── WebSocket ────────────────────────────────────────────


@app.websocket("/ws/stories/{story_id}")
async def story_websocket(ws: WebSocket, story_id: str):
    """WebSocket 实时推送 story 生成进度"""
    await ws.accept()
    # 查找 session
    session = None
    for s in await session_manager.list_sessions():
        if s.story_id == story_id:
            session = s
            break
    if not session:
        await ws.send_json({"type": "error", "message": "session not found"})
        await ws.close()
        return

    try:
        while True:
            # 骨架阶段：接收前端消息并简单响应
            data = await ws.receive_json()
            await ws.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        pass


# ─── 启动时恢复 session ───────────────────────────────────


@app.on_event("startup")
async def startup():
    # 可在此从磁盘恢复未完成的 session
    pass
