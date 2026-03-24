"""
Pydantic 模型定义
"""
from pydantic import BaseModel, Field
from typing import Literal


class StoryCreate(BaseModel):
    story_text: str = Field(..., description="输入的故事文本")
    mode: Literal["auto", "human"] = "auto"
    title: str | None = None


class StoryResponse(BaseModel):
    story_id: str
    session_id: str
    status: str
    mode: str


class AgentOutputResponse(BaseModel):
    agent: str
    output: dict


class InterventionRequest(BaseModel):
    action: Literal["confirm", "regenerate", "skip"]
    feedback: str | None = None


class WSMessage(BaseModel):
    type: str
    agent: str | None = None
    status: str | None = None
    output: dict | None = None
