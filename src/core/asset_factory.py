from pathlib import Path
from enum import Enum
from src.core.asset_manager import AssetManager
from src.store.redis_store import RedisAssetManager
from src.store.local_store import LocalAssetManager

class BackendType(Enum):
    REDIS = "redis"
    LOCAL = "local"

def create_asset_manager(backend: BackendType, **kwargs) -> AssetManager:
    """
    Create an asset manager instance based on the specified backend type.
    
    Args:
        backend (BackendType): Type of backend to use (LOCAL or REDIS)
        **kwargs: Additional arguments for asset manager configuration
            - base_path: Path for local storage (for LOCAL backend)
            - redis_url: URL for Redis connection (for REDIS backend)
            
    Returns:
        AssetManager: An instance of the appropriate asset manager
        
    Raises:
        ValueError: If an unknown backend type is provided
    """
    if backend == BackendType.LOCAL:
        return LocalAssetManager(kwargs.get("base_path", Path("assets")))
    elif backend == BackendType.REDIS:
        return RedisAssetManager(kwargs.get("redis_url", "redis://localhost:6379"))

    raise ValueError(f"Unknown backend type: {backend}")

def get_default_asset_manager(**kwargs) -> AssetManager:
    """
    Get a default asset manager, trying Redis first and falling back to local storage.
    
    Args:
        **kwargs: Additional arguments for asset manager configuration
        
    Returns:
        AssetManager: An instance of the appropriate asset manager
    """
    try:
        return create_asset_manager(BackendType.REDIS)
    except Exception:
        print("Failed to connect to Redis, falling back to local storage")
        return create_asset_manager(BackendType.LOCAL)
