from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from src.core.asset_manager import AssetManager,AssetType
from src.models.enums import ComponentType
class AssetReference(BaseModel):
    name: str
    storage_type: Literal["local", "redis"]
    asset_type: AssetType
    component_type: ComponentType
    cache_url: Optional[str] = None

    def get_url(self, asset_manager: AssetManager) -> str:
        return asset_manager.get_public_url(self.name, self.asset_type)