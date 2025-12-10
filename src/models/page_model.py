from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Dict, Any
from uuid import uuid4
from src.core.asset_manager import AssetManager,AssetType
from src.models.asset_model import AssetReference
from src.models.enums import ComponentType
from pathlib import Path
from datetime import datetime

class Component(BaseModel):
    type: ComponentType
    label: str
    config: Dict[str,Any] = Field(default_factory=dict)

    assets: List[AssetReference] = Field(default_factory=list)

    order: int = 0
    visible: bool = True

    @field_validator("config")
    def validate_config(cls, value):
        component_type = value.get('type')

        if component_type == ComponentType.WALL_PROJECTION:
            if 'view' not in value or value["view"] not in ["North", "South", "East", "West"]:
                raise ValueError("wall projection must include valid view")
        return value

class Page(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4().hex()))
    index: int = 0
    name: str
    components: List[Component] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1

    def add_component(self, component: Component):
        component.order = len(self.components)
        self.components.append(component)
        self.updated_at = datetime.now().isoformat()
        return self

    def reorder_components(self, order: List[int]):
        # Validate that the order list has the same length as components
        if len(order) != len(self.components):
            raise ValueError("Order list length must match components list length")

        # Validate that all indices are within the valid range
        if any(i < 0 or i >= len(self.components) for i in order):
            return self

        # Validate that the order list contains unique indices
        if len(set(order)) != len(order):
            raise ValueError("Order list must contain unique indices")

        # Create a new list with components in the specified order
        reordered_components = [self.components[i] for i in order]

        # Update the components list
        self.components = reordered_components
        self.updated_at = datetime.now().isoformat()

        # Update the order field of each component based on its new position
        for idx, component in enumerate(self.components):
            component.order = idx

        return self

    def to_dict(self):
        return self.model_dump()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

