from enum import Enum

class ViewType(Enum):
    BACK = "Back"
    FRONT = "Front"
    LEFT = "Left"
    RIGHT = "Right"
    TOP = "North"  # North is top
    BOTTOM = "South"  # South is bottom
    WEST = "West"  # West is left
    EAST = "East"  # East is right

class ComponentType(Enum):
    WALL_PROJECTION = "wall_projection"
    PANORAMA = "panorama"
    DATA_TABLE = "data_table"
    TEXT = "text"
    SIDE_PROJECTION = "side_projection"

class AvailableTemplates(Enum):
    BASE = "base"