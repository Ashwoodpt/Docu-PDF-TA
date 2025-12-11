from streamlit.components.v1 import components
from typing import Any, Optional, List, Dict, Union
import json
from src.render.template_engine import TemplateEngine
from pathlib import Path

homecomponent = components.declare_component(
    "homecomponent",
    path="./src/streamlit/dynamic/homecomponent",
)

def render_home_component(
        engine: TemplateEngine,
        context: Dict[str, Any],
        key: Optional[str] = None,
        events: bool = True,
) -> Optional[Dict[str, Any]]:
    rendered_html = engine.render(template_name="home.html", context=context)

    component_value = homecomponent(html = rendered_html, key=key, events=events, context=context)

    if events and component_value:
        try:
            if isinstance(component_value, dict) and 'value' in component_value:
                return component_value['value']
            elif isinstance(component_value, str):
                return json.loads(component_value)
            
        except Exception as e:
            print(e)
            return component_value
        
    return None