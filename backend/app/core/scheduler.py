"""
PipelineScheduler — 多 Story 并发调度器（B10）

核心职责：
- 全局任务队列管理
- Semaphore 控制实际并发执行数
- 排队状态推送（WebSocket）
- 公平调度（FIFO）
"""
import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Callable, Awaitable

from app.core.session import Session, SessionStatus, session_manager


@dataclass
class QueuedJob:
    """排队的 Pipeline 任务"""
    job_id: str
    session_id: str
    story_id: str
    mode: str
    initial_input: dict
    agent_llm_config: dict | None
    ws_send: Callable[[dict], Awaitable]  # WebSocket 推送回调
    position: int = 0  # 队列位置（1-based）
    future: asyncio.Future | None = None


class PipelineScheduler:
    """
    全局 Pipeline 调度器

    - 管理待执行任务队列（FIFO）
    - Semaphore 控制实际并发数
    - 自动拉取下一个任务执行
    - 推送队列状态到 WebSocket
    """

    def __init__(self, max_concurrent: int = 3):
        self._queue: asyncio.Queue[QueuedJob] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running: dict[str, QueuedJob] = {}  # job_id -> job
        self._workers: list[asyncio.Task] = []
        self._max_concurrent = max_concurrent
        self._started = False

    def start(self) -> None:
        """启动调度器（启动 N 个 worker）"""
        if self._started:
            return
        self._started = True
        for i in range(self._max_concurrent):
            task = asyncio.create_task(self._worker(i))
            self._workers.append(task)

    async def _worker(self, worker_id: int) -> None:
        """单个 worker：不断从队列取任务，执行，然后拉取下一个"""
        while True:
            job = await self._queue.get()
            async with self._semaphore:
                self._running[job.job_id] = job
                try:
                    # 推送开始执行
                    await job.ws_send({
                        "type": "job_started",
                        "story_id": job.story_id,
                        "job_id": job.job_id,
                    })

                    # 执行 Pipeline
                    await self._run_pipeline(job)

                except Exception as e:
                    await job.ws_send({
                        "type": "job_error",
                        "story_id": job.story_id,
                        "error": str(e),
                    })
                finally:
                    self._running.pop(job.job_id, None)
                    self._queue.task_done()
                    # 执行完后立即拉取下一个（如果有）
                    await self._notify_queue_positions()

    async def _run_pipeline(self, job: QueuedJob) -> None:
        """运行单个 story 的 pipeline"""
        from app.core.orchestrator import PipelineOrchestrator
        from app.agents import PIPELINE_AGENTS

        session = await session_manager.get_session(job.session_id)
        if not session:
            return

        orchestrator = PipelineOrchestrator(session=session, mode=job.mode)
        orchestrator.register_agents(PIPELINE_AGENTS)

        try:
            await orchestrator.run(job.story_id, job.initial_input, ws=job.ws_send)
        except Exception as e:
            await session_manager.update_status(session.session_id, SessionStatus.ERROR)
            raise

    async def submit(
        self,
        story_id: str,
        mode: str,
        initial_input: dict,
        agent_llm_config: dict | None,
        ws_send: Callable[[dict], Awaitable],
    ) -> str:
        """
        提交一个 story 生成任务到队列
        返回 job_id
        """
        job_id = str(uuid.uuid4())

        # 立即创建 session（不占 semaphore）
        session = await session_manager.create_session(story_id=story_id, mode=mode)

        job = QueuedJob(
            job_id=job_id,
            session_id=session.session_id,
            story_id=story_id,
            mode=mode,
            initial_input=initial_input,
            agent_llm_config=agent_llm_config,
            ws_send=ws_send,
        )

        # 加入队列
        await self._queue.put(job)

        # 更新队列中所有任务的 position
        await self._reassign_positions(job)

        # 推送排队状态
        await ws_send({
            "type": "job_queued",
            "story_id": story_id,
            "job_id": job_id,
            "position": job.position,
            "queue_size": self._queue.qsize(),
        })

        return job_id

    async def _reassign_positions(self, new_job: QueuedJob) -> None:
        """重新计算队列中所有任务的 position"""
        # 队列不支持遍历，我们用 running + 队列大小估算
        # 实际 position 在 _notify_queue_positions 中计算
        pass

    async def _notify_queue_positions(self) -> None:
        """推送所有排队任务的最新位置（仅推送 waiting 的任务）"""
        # 遍历队列找出等待中的任务（近似：running 之外的都是）
        # 由于 asyncio.Queue 不支持遍历，我们在 submit 时推送
        pass

    async def get_queue_status(self) -> dict:
        """获取当前队列状态"""
        return {
            "running_count": len(self._running),
            "queued_count": self._queue.qsize(),
            "max_concurrent": self._max_concurrent,
            "running_jobs": [
                {"job_id": j.job_id, "story_id": j.story_id} for j in self._running.values()
            ],
        }

    async def cancel_job(self, story_id: str) -> bool:
        """取消排队中的任务（如果尚未开始执行）"""
        # 遍历队列找到对应 job（asyncio.Queue 不直接支持，简化处理）
        # 骨架阶段：标记 session 为 error
        session = await session_manager.get_session_by_story_id(story_id)
        if session:
            await session_manager.update_status(session.session_id, SessionStatus.ERROR)
            return True
        return False


# 全局单例
scheduler = PipelineScheduler()
