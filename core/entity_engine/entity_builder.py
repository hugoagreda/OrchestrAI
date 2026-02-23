# OrchestrAI - Entity Builder v1
# Responsible for loading entity templates and generating entity configurations.

from pathlib import Path
import json
import yaml


class EntityBuilder:
    """
    EntityBuilder loads entity templates and prepares
    structured entity configurations for the runtime engine.
    """

    def __init__(self, templates_path="presets/entity_templates"):
        self.templates_path = Path(templates_path)

    # -------------------------
    # Load YAML Template
    # -------------------------
    def load_template(self, template_id: str) -> dict:
        template_file = self.templates_path / f"{template_id}.yaml"

        if not template_file.exists():
            raise FileNotFoundError(f"Template not found: {template_file}")

        with open(template_file, "r", encoding="utf-8") as f:
            template_data = yaml.safe_load(f)

        return template_data

    # -------------------------
    # Build Entity Instance
    # -------------------------
    def build_entity(self, template_id: str, overrides: dict | None = None) -> dict:
        """
        Creates a new entity configuration based on a template
        and optional override parameters.
        """

        entity = self.load_template(template_id)

        # Apply overrides (empresa o usuario)
        if overrides:
            entity = self._merge_dicts(entity, overrides)

        return entity

    # -------------------------
    # Helper: Deep Merge
    # -------------------------
    def _merge_dicts(self, base: dict, updates: dict) -> dict:
        for key, value in updates.items():
            if isinstance(value, dict) and key in base:
                base[key] = self._merge_dicts(base.get(key, {}), value)
            else:
                base[key] = value
        return base


# -------------------------
# Simple test run
# -------------------------
if __name__ == "__main__":
    builder = EntityBuilder()
    entity = builder.build_entity("human_ai_creator")

    print(json.dumps(entity, indent=2))