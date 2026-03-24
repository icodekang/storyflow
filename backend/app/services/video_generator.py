"""
VideoGenerator 服务抽象
支持 FFmpeg 本地 / Runway API / Pika API 切换
"""
import asyncio
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from app.core.config import settings


@dataclass
class VideoAsset:
    """视频素材"""
    asset_id: str
    prompt: str
    output_path: str
    status: Literal["pending", "generating", "done", "failed"] = "pending"
    error: str | None = None


class BaseVideoGenerator(ABC):
    """视频生成器基类"""

    @abstractmethod
    async def generate_image(self, prompt: str, output_path: str, **kwargs) -> VideoAsset:
        """生成单张图片"""
        raise NotImplementedError

    @abstractmethod
    async def generate_video_clip(self, prompt: str, output_path: str, duration_sec: int = 5, **kwargs) -> VideoAsset:
        """生成视频片段"""
        raise NotImplementedError


class FFmpegVideoGenerator(BaseVideoGenerator):
    """FFmpeg 本地视频生成（骨架阶段——生成占位文件）"""

    def __init__(self):
        self.ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    async def generate_image(self, prompt: str, output_path: str, **kwargs) -> VideoAsset:
        """骨架阶段：创建占位文件"""
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # 创建 1x1 黑色占位图
        if not self.ffmpeg_available:
            # 无 ffmpeg 时用 python 生成占位
            with open(output_path, "wb") as f:
                # Minimal 1x1 PNG
                f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")
        else:
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=black:size=1x1",
                "-frames:v", "1",
                output_path,
            ], capture_output=True)
        return VideoAsset(asset_id="", prompt=prompt, output_path=output_path, status="done")

    async def generate_video_clip(self, prompt: str, output_path: str, duration_sec: int = 5, **kwargs) -> VideoAsset:
        """骨架阶段：创建占位 MP4"""
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if self.ffmpeg_available:
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=black:size=512x512:duration={duration_sec}",
                "-c:v", "libx264", "-t", str(duration_sec),
                "-pix_fmt", "yuv420p",
                output_path,
            ], capture_output=True)
        return VideoAsset(asset_id="", prompt=prompt, output_path=output_path, status="done")


class RunwayVideoGenerator(BaseVideoGenerator):
    """Runway API 视频生成（真实 API 接入时启用）"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.RUNWAY_API_KEY

    async def generate_image(self, prompt: str, output_path: str, **kwargs) -> VideoAsset:
        # TODO: 调用 Runway Gen-2/Gen-3 API
        return VideoAsset(asset_id="", prompt=prompt, output_path=output_path, status="done")

    async def generate_video_clip(self, prompt: str, output_path: str, duration_sec: int = 5, **kwargs) -> VideoAsset:
        # TODO: 调用 Runway API
        return VideoAsset(asset_id="", prompt=prompt, output_path=output_path, status="done")


# 工厂函数
def get_video_generator() -> BaseVideoGenerator:
    mode = settings.VIDEO_GENERATOR_MODE
    if mode == "ffmpeg":
        return FFmpegVideoGenerator()
    elif mode == "runway":
        return RunwayVideoGenerator()
    else:
        return FFmpegVideoGenerator()  # 默认降级


# 全局单例
video_generator = get_video_generator()
