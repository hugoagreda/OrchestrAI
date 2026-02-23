# OrchestrAI - Entity Runtime v1
# Combines identity and behavior into a runtime-ready entity.

from core.entity_engine.entity_builder import EntityBuilder
from core.identity_engine.identity_engine import IdentityEngine
from core.behavior_engine.behavior_engine import BehaviorEngine


class EntityRuntime:
    """
    Builds a runtime-ready entity combining
    identity and behavior layers.
    """

    def __init__(self):
        self.builder = EntityBuilder()
        self.identity_engine = IdentityEngine()
        self.behavior_engine = BehaviorEngine()

    # -------------------------
    # Create Runtime Entity
    # -------------------------
    def create_runtime(self, template_id: str, overrides: dict | None = None) -> dict:
        entity = self.builder.build_entity(template_id, overrides)

        runtime_identity = self.identity_engine.build_runtime_identity(entity)
        runtime_behavior = self.behavior_engine.build_runtime_behavior(entity)

        runtime_entity = {
            "entity_id": entity.get("id"),
            "entity_type": entity.get("entity_type"),
            "identity": runtime_identity,
            "behavior": runtime_behavior,
        }

        return runtime_entity


# Manual test
if __name__ == "__main__":
    runtime = EntityRuntime()
    entity_runtime = runtime.create_runtime("human_ai_creator")

    print(entity_runtime)