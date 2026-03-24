"""
pi-mono 三层记忆系统
- 短期：Agent 消息历史（in-memory deque）
- 中期：Session JSON 文件
- 长期：ChromaDB 向量检索
"""
import json
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

import aiofiles

if TYPE_CHECKING:
    from app.core.session import Session

# ─── 短期记忆 ────────────────────────────────────────────


class ShortTermMemory:
    """短期记忆：基于列表，保存 Agent 消息历史"""

    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages
        self._messages: list[dict[str, Any]] = []

    def append(self, role: str, content: Any) -> None:
        self._messages.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        if len(self._messages) > self.max_messages:
            self._messages.pop(0)

    def get_all(self) -> list[dict[str, Any]]:
        return list(self._messages)

    def get_last(self, n: int) -> list[dict[str, Any]]:
        return self._messages[-n:]

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)


# ─── 中期记忆 ────────────────────────────────────────────


class MediumTermMemory:
    """中期记忆：每个 Session 一个 JSON 文件"""

    def __init__(self, session: "Session"):
        self.session = session
        self._path = f"data/memory/sessions/{session.session_id}.json"
        self._cache: dict | None = None

    async def _load(self) -> dict:
        if self._cache is not None:
            return self._cache
        try:
            async with aiofiles.open(self._path, "r", encoding="utf-8") as f:
                self._cache = json.loads(await f.read())
        except FileNotFoundError:
            self._cache = {
                "session_id": self.session.session_id,
                "story_id": self.session.story_id,
                "history": [],
            }
        return self._cache

    async def _save(self, data: dict) -> None:
        import os
        os.makedirs(f"data/memory/sessions", exist_ok=True)
        async with aiofiles.open(self._path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        self._cache = data

    async def append(self, agent_name: str, output: dict) -> None:
        data = await self._load()
        data["history"].append({
            "agent": agent_name,
            "output": output,
            "timestamp": datetime.now().isoformat(),
        })
        await self._save(data)

    async def get_history(self, agent_name: str | None = None) -> list[dict]:
        data = await self._load()
        if agent_name is None:
            return data["history"]
        return [h for h in data["history"] if h["agent"] == agent_name]

    async def get_all(self) -> dict:
        return await self._load()


# ─── 长期记忆 ────────────────────────────────────────────


class LongTermMemory:
    """长期记忆：ChromaDB 向量检索"""

    def __init__(self):
        self._client = None
        self._collection = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        import chromadb
        from app.core.config import settings
        self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self._collection = self._client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    async def add(self, session_id: str, agent_name: str, content: Any) -> None:
        """写入长期记忆"""
        collection = self._get_collection()
        text = json.dumps(content, ensure_ascii=False)
        collection.add(
            ids=[str(uuid.uuid4())],
            documents=[text],
            metadatas=[{
                "session_id": session_id,
                "agent_name": agent_name,
                "timestamp": datetime.now().isoformat(),
            }],
        )

    async def search(self, query: str, top_k: int = 3, session_id: str | None = None) -> list[dict]:
        """向量相似度检索"""
        collection = self._get_collection()
        where_filter = {"session_id": session_id} if session_id else None
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
        )
        hits = []
        if results and results["documents"]:
            for doc, meta in zip(results["documents"], results["metadatas"]):
                hits.append({"content": json.loads(doc), "metadata": meta})
        return hits


# ─── MemoryLayer 聚合 ─────────────────────────────────────


class MemoryLayer:
    """三层记忆聚合接口"""

    def __init__(self, session: "Session"):
        self.session = session
        self.short = ShortTermMemory()
        self.medium = MediumTermMemory(session)
        self.long = LongTermMemory()

    async def search(self, query: str, top_k: int = 3) -> list[dict]:
        """检索长期记忆"""
        return await self.long.search(
            query=query,
            top_k=top_k,
            session_id=self.session.session_id,
        )

    async def add(self, agent_name: str, output: dict) -> None:
        """写入中期 + 长期记忆"""
        await self.medium.append(agent_name, output)
        await self.long.add(
            session_id=self.session.session_id,
            agent_name=agent_name,
            content=output,
        )

    async def get_context_for_agent(self, agent_name: str) -> dict:
        """为某个 Agent 准备完整的上下文"""
        medium = await self.medium.get_history(agent_name)
        return {"medium_term": medium}

    async def persist(self) -> None:
        """持久化中期记忆"""
        # MediumTermMemory 会自动持久化，调用一次确保落盘
        await self.medium.get_all()
