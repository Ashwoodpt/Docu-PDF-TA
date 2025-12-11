from streamlit.components.v1 import components
from typing import Any, Optional, Dict
import json
from src.render.template_engine import TemplateEngine

page_list_component = components.declare_component(
    "page_list_component",
    path="./src/streamlit/dynamic/page_list_component",
)

def render_page_list_component(
        engine: TemplateEngine,
        context: Dict[str, Any],
        key: Optional[str] = None,
        events: bool = True,
) -> Optional[Dict[str, Any]]:
    rendered_html = engine.render(template_name="components/page_list.html", context=context)
    # Only pass JSON-serializable data to the component, not the entire context
    component_value = page_list_component(html = rendered_html, key=key, events=events)

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
