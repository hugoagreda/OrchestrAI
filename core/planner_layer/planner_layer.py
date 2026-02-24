# Responsible for interpreting runtime entity configuration
# and generating a structured high-level action plan (IntentStep).

from core.planner_layer.intent_step import IntentStep


class PlannerLayer:
    """
    PlannerLayer reads runtime entity identity + behavior
    and produces an execution intent (NOT workflows).
    """

    def __init__(self):
        pass

    # -------------------------------------------------
    # Generate Action Plan (IntentStep)
    # -------------------------------------------------
    def generate_plan(self, runtime_entity: dict) -> IntentStep:

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
        plan_data = {
            "objective": primary_goal,
            "content_type": content_type,
            "platform": platform,
            "tone": tone,
            "visual_style": style,
        }

        # 🔥 DEVUELVE IntentStep (ya no dict crudo)
        return IntentStep(plan_data)


# -------------------------------------------------
# Manual test
# -------------------------------------------------
if __name__ == "__main__":
    from core.entity_engine.entity_runtime import EntityRuntime

    runtime_engine = EntityRuntime()
    planner = PlannerLayer()

    runtime_entity = runtime_engine.create_runtime("human_ai_creator")

    action_plan = planner.generate_plan(runtime_entity)

    # 👇 ahora es objeto, no dict
    print(action_plan.to_dict())