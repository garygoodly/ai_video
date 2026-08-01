from pathlib import Path

from jinja2 import Template


class PromptService:

    def render(
        self,
        template_path: str,
        context: dict,
    ) -> str:

        template = Path(template_path).read_text(
            encoding="utf-8"
        )

        return Template(template).render(**context)