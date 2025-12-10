import numpy as np
import math
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from typing import List, Tuple, Optional


DIRECTION_MAP = {
    (0, -1): "Back",
    (1, 0): "Right",
    (-1, 0): "Left",
    (0, 1): "Front"
}


def calculate_wall_normals(walls_data: List[List[Tuple[float, float]]]) -> List[dict]:
    """
    Calculate facing direction for each wall from its 4 corner points.
    """
    all_wall_polygons = [Polygon(wall) for wall in walls_data]
    new_wall_data = [None] * len(walls_data)

    for i, wall in enumerate(walls_data):
        midpoint, normal1, normal2, longest_idx = _get_longest_segment(wall)

        hit1 = _ray_intersects_walls(midpoint, normal1, i, all_wall_polygons)
        hit2 = _ray_intersects_walls(midpoint, normal2, i, all_wall_polygons)

        if not hit1:
            exterior_normal = normal1
            clean_normal = np.round(exterior_normal).astype(int)
            new_wall_data[i] = {"corners": wall, "facing": _normal_to_direction(clean_normal)}
        elif not hit2:
            exterior_normal = normal2
            clean_normal = np.round(exterior_normal).astype(int)
            new_wall_data[i] = {"corners": wall, "facing": _normal_to_direction(clean_normal)}
        else:
            new_wall_data[i] = {"corners": wall, "facing": "inner"}
    return new_wall_data


def _get_longest_segment(wall_pts: List[Tuple[float, float]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """Find the longest edge of a wall quadrilateral and calculate its normal vectors."""
    pts = np.array(wall_pts)
    next_pts = np.roll(pts, -1, axis=0)
    edges = next_pts - pts
    lengths = np.linalg.norm(edges, axis=1)
    longest_idx = np.argmax(lengths)

    # Edge direction and midpoint
    direction = edges[longest_idx]
    midpoint = (pts[longest_idx] + next_pts[longest_idx]) / 2

    # Normal vector (perpendicular to direction)
    norm_direction = direction / lengths[longest_idx]

    # Two possible unit normals
    normal1 = np.array([-norm_direction[1], norm_direction[0]])
    normal2 = np.array([norm_direction[1], -norm_direction[0]])

    return midpoint, normal1, normal2, longest_idx


def _ray_intersects_walls(midpoint: np.ndarray, direction: np.ndarray, exclude_wall_idx: int, all_walls: List[Polygon]) -> bool:
    """Check if a ray from a wall's midpoint intersects with any other wall."""
    ray_end = midpoint + direction * 10000  # Extend ray far enough
    ray = LineString([midpoint, ray_end])

    for i, wall_polygon in enumerate(all_walls):
        if i == exclude_wall_idx:
            continue

        if ray.intersects(wall_polygon.boundary):
            intersection_points = ray.intersection(wall_polygon.boundary)

            # Check if intersection exists and is not just the starting point
            if intersection_points.geom_type == 'Point':
                # Single point intersection - check if it's not the starting point
                return not Point(midpoint).equals(intersection_points)
            elif hasattr(intersection_points, 'geoms'):
                # Multiple geometries - check if any is a point not at the start
                for geom in intersection_points.geoms:
                    if geom.geom_type == 'Point' and not Point(midpoint).equals(geom):
                        return True
            elif intersection_points.geom_type == 'LineString':
                # Line intersection - any non-empty intersection counts
                return not intersection_points.is_empty

    return False


def _normal_to_direction(normal: np.ndarray) -> str:
    """Convert a normal vector to a compass direction string."""
    x, y = normal

    if x == 0 and y == 1: return "Front"
    if x == 0 and y == -1: return "Back"
    if x == 1 and y == 0: return "Right"
    if x == -1 and y == 0: return "Left"

    angle = math.degrees(math.atan2(y, x))
    if angle < 0:
        angle += 360

    if 22.5 <= angle < 67.5: return "SouthEast"
    elif 67.5 <= angle < 112.5: return "South"
    elif 112.5 <= angle < 157.5: return "SouthWest"
    elif 157.5 <= angle < 202.5: return "West"
    elif 202.5 <= angle < 247.5: return "NorthWest"
    elif 247.5 <= angle < 292.5: return "North"
    elif 292.5 <= angle < 337.5: return "NorthEast"
    else: return "East"


def calculate_viewbox(walls: List[List[Tuple[float, float]]], padding: int = 50) -> dict:
    """Calculate the SVG viewbox based on all wall coordinates."""
    all_x = []
    all_y = []

    for wall in walls:
        for x, y in wall:
            all_x.append(x)
            all_y.append(y)

    min_x = min(all_x)
    min_y = min(all_y)
    max_x = max(all_x)
    max_y = max(all_y)

    width = max_x - min_x
    height = max_y - min_y

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    return {
        "dimensions": f"{min_x - padding} {min_y - padding} {width + padding * 2} {height + padding * 2}",
        "center": (center_x, center_y)
    }