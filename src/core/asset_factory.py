from pathlib import Path
from enum import Enum
from src.core.asset_manager import AssetManager
from src.store.redis_store import RedisAssetManager
from src.store.local_store import LocalAssetManager

class BackendType(Enum):
    REDIS = "redis"
    LOCAL = "local"

def create_asset_manager(backend: BackendType, **kwargs) -> AssetManager:
    if backend == BackendType.LOCAL:
        return LocalAssetManager(kwargs.get("base_path", Path("assets")))
    elif backend == BackendType.REDIS:
        return RedisAssetManager(kwargs.get("redis_url", "redis://localhost:6379"))

    raise ValueError(f"Unknown backend type: {backend}")

def get_default_asset_manager(**kwargs) -> AssetManager:
    try:
        return create_asset_manager(BackendType.REDIS)
    except Exception:
        print("Failed to connect to Redis, falling back to local storage")
        return create_asset_manager(BackendType.LOCAL)
