# OrchestrAI - Behavior Engine v1
# Responsible for interpreting entity behavior configuration.


class BehaviorEngine:
    """
    Converts entity behavior configuration into runtime behavior rules.
    """

    def __init__(self):
        pass

    # -------------------------
    # Extract Behavior
    # -------------------------
    def extract_behavior(self, entity: dict) -> dict:
        if "behavior" not in entity:
            raise ValueError("Entity has no behavior layer.")
        return entity["behavior"]

    # -------------------------
    # Normalize Behavior
    # -------------------------
    def normalize_behavior(self, behavior: dict) -> dict:

    # 🔥 Copia completa del behavior original
        normalized = dict(behavior)

    # Solo aseguramos defaults, sin borrar nada
        normalized.setdefault("primary_goal", "undefined")
        normalized.setdefault("secondary_goals", [])
        normalized.setdefault("autonomy_level", "low")
        normalized.setdefault("allowed_actions", [])
        normalized.setdefault("restricted_actions", [])

        return normalized

    # -------------------------
    # Build Runtime Behavior
    # -------------------------
    def build_runtime_behavior(self, entity: dict) -> dict:
        behavior = self.extract_behavior(entity)
        return self.normalize_behavior(behavior)


# Manual test
if __name__ == "__main__":
    from core.entity_engine.entity_builder import EntityBuilder

    builder = EntityBuilder()
    engine = BehaviorEngine()

    entity = builder.build_entity("human_ai_creator")
    print(engine.build_runtime_behavior(entity))