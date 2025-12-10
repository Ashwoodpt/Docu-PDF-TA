from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any
import datetime

class TemplateEngine:
    def __init__(self, templates_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        # Add custom filters
        self.env.filters['to_date'] = self._to_date_filter
        self.env.filters['to_upper'] = self._to_upper_filter

    def render(self, template_name: str, context: Dict[str, Any]) -> str:

        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_to_file(self, template_name: str, context: Dict[str, Any], output_path: Path) -> None:

        rendered_html = self.render(template_name, context)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        return output_path
    def add_global(self, name: str, obj: Any) -> None:

        self.env.globals[name] = obj

    def _to_date_filter(self, value: Any, format_string: str = "%Y-%m-%d") -> str:

        if isinstance(value, datetime.datetime):
            return value.strftime(format_string)
        elif isinstance(value, datetime.date):
            return value.strftime(format_string)
        elif isinstance(value, str):
            return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(format_string)
        return str(value)

    def _to_upper_filter(self, value: str) -> str:
        return str(value).upper()

if __name__ == "__main__":
    # Example usage
    templates_path = Path(__file__).parent.parent / "templates"
    engine = TemplateEngine(templates_path)

    # Example context data
    context = {
        "css_url": "/static/css/main.css",
        "header_logo_url": "/static/images/logo.svg",
        "powered_by_logo_url": "/static/images/powered_by.svg",
        "generation_date": datetime.datetime.now().isoformat(),
        "page_number": 1,
        "total_pages": 10,
    }

    # Render a template
    html_output = engine.render("base.html", context)
    print(html_output)