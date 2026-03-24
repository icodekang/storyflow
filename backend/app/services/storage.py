"""
StorageService 抽象
支持本地文件系统 / OSS（阿里云/腾讯云）切换
"""
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings


class BaseStorageService(ABC):
    """存储服务基类"""

    @abstractmethod
    async def save(self, content: bytes, path: str) -> str:
        """保存文件，返回访问 URL"""
        raise NotImplementedError

    @abstractmethod
    async def get(self, path: str) -> bytes:
        """读取文件内容"""
        raise NotImplementedError

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, path: str) -> None:
        """删除文件"""
        raise NotImplementedError

    @abstractmethod
    async def list(self, prefix: str = "") -> list[str]:
        """列出 prefix 下的文件"""
        raise NotImplementedError


class LocalStorageService(BaseStorageService):
    """本地文件系统存储"""

    def __init__(self, root: str | None = None):
        self.root = Path(root or settings.STORAGE_LOCAL_ROOT)

    def _full_path(self, path: str) -> Path:
        return self.root / path.lstrip("/")

    async def save(self, content: bytes, path: str) -> str:
        full = self._full_path(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full, "wb") as f:
            await f.write(content)
        return f"/storage/{path}"

    async def get(self, path: str) -> bytes:
        full = self._full_path(path)
        async with aiofiles.open(full, "rb") as f:
            return await f.read()

    async def exists(self, path: str) -> bool:
        return self._full_path(path).exists()

    async def delete(self, path: str) -> None:
        full = self._full_path(path)
        if full.exists():
            full.unlink()

    async def list(self, prefix: str = "") -> list[str]:
        full = self._full_path(prefix)
        if not full.exists():
            return []
        if full.is_file():
            return [prefix]
        return [str(p.relative_to(self.root)).replace("\\", "/")
                for p in full.rglob("*") if p.is_file()]


import aiofiles


class OSSStorageService(BaseStorageService):
    """OSS 对象存储（骨架阶段——占位）"""

    def __init__(self, bucket: str = "storyflow"):
        self.bucket = bucket
        # TODO: 接入阿里云 OSS 或腾讯云 COS

    async def save(self, content: bytes, path: str) -> str:
        # TODO: 调用 OSS 上传
        return f"https://{self.bucket}.oss-cn-hangzhou.aliyuncs.com/{path}"

    async def get(self, path: str) -> bytes:
        # TODO: 调用 OSS 下载
        return b""

    async def exists(self, path: str) -> bool:
        return False

    async def delete(self, path: str) -> None:
        pass

    async def list(self, prefix: str = "") -> list[str]:
        return []


def get_storage_service() -> BaseStorageService:
    mode = settings.STORAGE_MODE
    if mode == "oss":
        return OSSStorageService()
    return LocalStorageService()


# 全局单例
storage = get_storage_service()
