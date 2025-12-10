from lxml import etree
from typing import List,Tuple

from src.geom_utils.geometry_calculator import calculate_wall_normals, calculate_viewbox


def generate_wall_projection_svg(wall_data: List[List[Tuple[float, float]]], highlight_direction: List[str]) -> etree._Element:
    """
    Generate an SVG representation of wall projections with optional highlighting.
    
    Args:
        wall_data: A list of walls, where each wall is represented as a list of (x, y) coordinate tuples
        highlight_direction: A list of directions to highlight (e.g., ["North", "South"])
        
    Returns:
        An lxml etree Element representing the SVG
    """
    # Create WallsData from the input dict
    processed_walls_data = calculate_wall_normals(wall_data)

    # The calculate_viewbox function expects a list of walls where each wall is a list of [x, y] coordinates
    # After calculate_wall_normals, each wall is a dict with "corners" and "facing" keys
    wall_corners_list = [wall["corners"] for wall in processed_walls_data if isinstance(wall, dict) and "corners" in wall]

    viewbox = calculate_viewbox(wall_corners_list)

    root = etree.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "viewBox": viewbox["dimensions"],
        "style": "background: transparent;"
    })

    walls_layer = etree.SubElement(root, "g", id="walls-layer")
    highlight_layer = etree.SubElement(root, "g", id="highlight-layer")

    for i, wall in enumerate(processed_walls_data):
        isHighlighted = wall["facing"] in highlight_direction
        wall_polygon = _create_polygon(wall["corners"], isHighlighted)
        if isHighlighted:
            highlight_layer.append(wall_polygon)
            continue
        walls_layer.append(wall_polygon)

    return root


def _create_polygon(corners: List[Tuple[float, float]], isHighlighted: bool) -> etree._Element:
    """
    Create an SVG polygon element for a wall.
    
    Args:
        corners: A list of (x, y) coordinate tuples representing the corners of the wall
        isHighlighted: Whether this wall should be highlighted (different color)
        
    Returns:
        An lxml etree Element representing the polygon
    """
    wall_polygon = etree.Element("path", {
        "d": f"M {corners[0][0]} {corners[0][1]} L {corners[1][0]} {corners[1][1]} L {corners[2][0]} {corners[2][1]} L {corners[3][0]} {corners[3][1]} Z",
        "fill": "#259DC9" if isHighlighted else "#000",  # Using gray for non-highlighted walls
        "stroke": "#259DC9" if isHighlighted else "#000",  # Using gray for non-highlighted walls
        "stroke-width": "2",
    })

    return wall_polygon


if __name__ == "__main__":
    import json
    from pathlib import Path
    # Load from file for testing
    walls_data_dict = json.loads(Path("assets/wall_data.json").read_text())
    svg = generate_wall_projection_svg(walls_data_dict, ["North"])
    Path("assets/wall_projection.svg").write_text(etree.tostring(svg, encoding="unicode", method="xml").strip())
