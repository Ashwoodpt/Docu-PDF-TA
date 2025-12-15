from typing import Protocol, runtime_checkable
from enum import Enum

class AssetType(Enum):
    SVG = "svg"
    JSON = "json"
    CSV = "csv"
    IMG = "img"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    PDF = "pdf"


@runtime_checkable
class AssetManager(Protocol):

    def save(self, name: str, content: bytes, asset_type: AssetType) -> str:
        raise NotImplementedError

    def get(self, name: str, asset_type: AssetType) -> bytes:
        raise NotImplementedError
    
    def exists(self, name: str, asset_type: AssetType) -> bool:
        raise NotImplementedError
    
    def list(self, asset_type: AssetType) -> list[str]:
        raise NotImplementedError
    
    def delete(self, name: str, asset_type: AssetType) -> None:
        raise NotImplementedError
    
    def get_public_url(self, name: str, asset_type: AssetType) -> str:
        raise NotImplementedError
    
    def health_check(self) -> bool:
        raise NotImplementedError