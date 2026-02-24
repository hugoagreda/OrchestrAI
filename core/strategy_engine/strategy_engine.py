class StrategyEngine:

    def apply_strategy(self, intent_step, runtime_entity: dict):

        workflow_profile = runtime_entity.get("workflow_profile", {})

        intent_data = intent_step.to_dict()

        # -------------------------------------------------
        # Media generation toggle
        # -------------------------------------------------
        if workflow_profile.get("media_generation") == "disabled":

            restricted_caps = intent_data.get("restricted_capabilities", [])
            restricted_caps.append("media.*")

            intent_data["restricted_capabilities"] = restricted_caps

        # -------------------------------------------------
        # Publishing optional
        # -------------------------------------------------
        if workflow_profile.get("publishing") == "optional":
            intent_data["publishing_optional"] = True

        # -------------------------------------------------
        # Analytics feedback
        # -------------------------------------------------
        if workflow_profile.get("analytics_feedback") == "enabled":
            intent_data["analytics_enabled"] = True

        return intent_step.__class__(intent_data)