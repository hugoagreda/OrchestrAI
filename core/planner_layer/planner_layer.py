# OrchestrAI - Planner Layer v2
# Responsible for interpreting runtime entity configuration
# and generating a structured high-level action plan.


class PlannerLayer:
    """
    PlannerLayer reads runtime entity identity + behavior
    and produces an execution intent (NOT workflows).
    """

    def __init__(self):
        pass

    # -------------------------
    # Generate Action Plan
    # -------------------------
    def generate_plan(self, runtime_entity: dict) -> dict:

        identity = runtime_entity.get("identity", {})
        behavior = runtime_entity.get("behavior", {})

        # -------------------------------------------------
        # Extract Intent from Behavior (NO hardcoded logic)
        # -------------------------------------------------
        primary_goal = behavior.get("primary_goal", "undefined")

        # These should ideally come from behavior templates
        content_type = behavior.get("content_format", "generic")
        platform = behavior.get("platform", "generic")

        # -------------------------------------------------
        # Identity-driven modifiers (stylistic only)
        # -------------------------------------------------
        style = identity.get("style", "realistic")
        tone = identity.get("voice", {}).get("tone", "natural")

        # -------------------------------------------------
        # Structured Action Plan (INTENT, not EXECUTION)
        # -------------------------------------------------
        plan = {
            "objective": primary_goal,
            "content_type": content_type,
            "platform": platform,
            "tone": tone,
            "visual_style": style,
        }

        return plan


# -------------------------
# Manual test
# -------------------------
if __name__ == "__main__":
    from core.entity_engine.entity_runtime import EntityRuntime

    runtime_engine = EntityRuntime()
    planner = PlannerLayer()

    runtime_entity = runtime_engine.create_runtime("human_ai_creator")

    action_plan = planner.generate_plan(runtime_entity)

    print(action_plan)