import redis
import json
from pathlib import Path
from typing import Dict, Any
from src.core.asset_manager import AssetManager,AssetType
import shutil

class RedisAssetManager:
    def __init__(self, redis_url: str = None) -> None:
        # Default to localhost if no URL is provided, but allow environment variable override
        if redis_url is None:
            import os
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis.from_url(redis_url, decode_responses=False)
        self._key_prefix = "asset:"

        try:
            self.client.ping()
        except redis.exceptions.ConnectionError:
            raise Exception(f"Failed to connect to Redis at {redis_url}")

    def _make_key(self, name: str, asset_type: AssetType) -> str:
        return f"{self._key_prefix}{asset_type.value}:{name}"

    def save(self, name: str, content: bytes, asset_type: AssetType) -> str:
        key = self._make_key(name, asset_type)
        metadata = {
            "name": name,
            "type": asset_type.value,
            "size": len(content)
        }

        self.client.setex(key,3600, json.dumps({"metadata": metadata, "content": content.decode("utf-8") if asset_type == AssetType.SVG else content.hex()}))

        return self.get_public_url(name, asset_type)

    def get(self, name: str, asset_type: AssetType) -> bytes:
        key = self._make_key(name, asset_type)
        data = self.client.get(key)

        if data is None:
            raise FileNotFoundError(f"Asset '{name}' {asset_type.value} not found")

        decoded = json.loads(data)

        if asset_type == AssetType.SVG:
            return decoded["content"].encode("utf-8")
        else:
            return bytes.fromhex(decoded["content"])

    def exists (self, name: str, asset_type: AssetType) -> bool:
        key = self._make_key(name, asset_type)
        return self.client.exists(key)

    def list(self, asset_type: AssetType) -> list[str]:
        pattern = f"{self._key_prefix}{asset_type.value}:*" if asset_type else f"{self._key_prefix}*"

        keys = self.client.keys(pattern)
        # Decode bytes to string and remove prefix
        return [key.decode('utf-8')[len(self._key_prefix):] for key in keys]

    def delete(self, name: str, asset_type: AssetType) -> None:
        key = self._make_key(name, asset_type)
        print(key)
        self.client.delete(key)

    def get_public_url(self, name: str, asset_type: AssetType) -> str:
        import base64
        import urllib.parse

        # Get the content from Redis
        content = self.get(name, asset_type)

        # For images, return as data URL
        if asset_type in [AssetType.IMG, AssetType.PNG, AssetType.JPG, AssetType.JPEG]:
            # For binary images, return as base64 data URL
            encoded = base64.b64encode(content).decode('utf-8')
            mime_type = "image/jpeg" if asset_type in [AssetType.JPG, AssetType.JPEG] else "image/png"
            return f"data:{mime_type};base64,{encoded}"

        # For SVG content, return as data URL
        elif asset_type == AssetType.SVG:
            # For SVG, return the raw content as a data URL
            content_str = content.decode('utf-8')
            # For SVG content, it's more reliable to use base64 encoding instead of URL encoding
            # which can have issues with complex SVG content
            encoded = base64.b64encode(content).decode('utf-8')
            return f"data:image/svg+xml;base64,{encoded}"

        # For other types, also use data URLs where appropriate
        elif asset_type == AssetType.PDF:
            encoded = base64.b64encode(content).decode('utf-8')
            return f"data:application/pdf;base64,{encoded}"

        # Fallback to temporary file approach for other cases if needed
        temp_dir = Path("temp_assets") / asset_type.value
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_path = temp_dir / name

        if not temp_path.exists():
            temp_path.write_bytes(content)

        return f"{temp_path.absolute()}"
    
    def health_check(self):
        """
        Check if the Redis connection is healthy by pinging the server.
        
        Returns:
            bool: True if the Redis server responds to ping, False otherwise
        """
        return self.client.ping()

    def clear_temp_cache(self):
        """
        Clear the temporary asset cache directory if it exists.
        This removes all temporary files created during asset serving.
        """
        if Path("temp_assets").exists():
            shutil.rmtree("temp_assets")