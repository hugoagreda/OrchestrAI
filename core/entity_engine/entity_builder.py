# OrchestrAI - Entity Builder v1
# Loads entity templates and builds base entity definitions.

from pathlib import Path
import yaml


class EntityBuilder:
    """
    Loads entity templates and prepares entity definitions.
    """

    def __init__(self, templates_path="presets/entity_templates"):
        self.templates_path = Path(templates_path)

    # -------------------------
    # Load Template
    # -------------------------
    def load_template(self, template_id: str) -> dict:
        template_file = self.templates_path / f"{template_id}.yaml"

        if not template_file.exists():
            raise FileNotFoundError(f"Template not found: {template_file}")

        with open(template_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # -------------------------
    # Build Entity
    # -------------------------
    def build_entity(self, template_id: str, overrides: dict | None = None) -> dict:
        entity = self.load_template(template_id)

        if overrides:
            entity = self._merge_dicts(entity, overrides)

        return entity

    # -------------------------
    # Deep Merge Helper
    # -------------------------
    def _merge_dicts(self, base: dict, updates: dict) -> dict:
        for key, value in updates.items():
            if isinstance(value, dict) and key in base:
                base[key] = self._merge_dicts(base.get(key, {}), value)
            else:
                base[key] = value
        return base


# Manual test
if __name__ == "__main__":
    builder = EntityBuilder()
    entity = builder.build_entity("human_ai_creator")
    print(entity)