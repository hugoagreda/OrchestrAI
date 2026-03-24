# Summary: Implements behavior engine logic for the OrchestrAI runtime.
# Responsible for interpreting entity behavior configuration
# and enriching IntentStep without executing logic.


class BehaviorEngine:

    def __init__(self):
        pass

    # -------------------------------------------------
    # Extract Behavior
    # -------------------------------------------------
    def extract_behavior(self, entity: dict) -> dict:
        if "behavior" not in entity:
            raise ValueError("Entity has no behavior layer.")
        return entity["behavior"]

    # -------------------------------------------------
    # Normalize Behavior (non-destructive)
    # -------------------------------------------------
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

    # -------------------------------------------------
    # Build Runtime Behavior
    # -------------------------------------------------
    def build_runtime_behavior(self, entity: dict) -> dict:
        behavior = self.extract_behavior(entity)
        return self.normalize_behavior(behavior)

    # -------------------------------------------------
    # 🔥 NEW — Adapt IntentStep (Planner → Behavior Bridge)
    # -------------------------------------------------
    def adapt_intent(self, intent_step, runtime_entity: dict):
   
        behavior = runtime_entity.get("behavior", {})

        # Convertimos a dict para modificar sin romper estructura
        intent_data = intent_step.to_dict()

        # Ejemplo simple (no hardcodear lógica compleja aún)
        autonomy = behavior.get("autonomy_level", "medium")

        # Añadimos metadata futura
        intent_data["autonomy"] = autonomy

        intent_data["allowed_actions"] = behavior.get("allowed_actions", [])
        intent_data["restricted_actions"] = behavior.get("restricted_actions", [])
        intent_data["restricted_capabilities"] = behavior.get("restricted_capabilities", [])

        # 🔥 Devolvemos nuevo IntentStep (inmutable conceptualmente)
        return intent_step.__class__(intent_data)