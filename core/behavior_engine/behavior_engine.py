# OrchestrAI - Identity Engine v1
# Responsible for interpreting identity configuration
# and preparing runtime identity data.


class IdentityEngine:
    """
    Interprets the identity layer of an entity definition
    and converts it into a runtime-ready structure.
    """

    def __init__(self):
        pass

    # -------------------------
    # Extract Identity
    # -------------------------
    def extract_identity(self, entity: dict) -> dict:
        if "identity" not in entity:
            raise ValueError("Entity has no identity layer.")
        return entity["identity"]

    # -------------------------
    # Normalize Identity
    # -------------------------
    def normalize_identity(self, identity: dict) -> dict:
        normalized = {
            "style": identity.get("style", "realistic"),
            "persona_name": identity.get("persona_name", "Unnamed Entity"),
            "archetype": identity.get("archetype", "generic_creator"),
            "visual_profile": identity.get("visual_profile", {}),
            "voice": identity.get("voice", {}),
        }
        return normalized

    # -------------------------
    # Build Runtime Identity
    # -------------------------
    def build_runtime_identity(self, entity: dict) -> dict:
        identity = self.extract_identity(entity)
        return self.normalize_identity(identity)


# Manual test
if __name__ == "__main__":
    from core.entity_engine.entity_builder import EntityBuilder

    builder = EntityBuilder()
    engine = IdentityEngine()

    entity = builder.build_entity("human_ai_creator")
    print(engine.build_runtime_identity(entity))