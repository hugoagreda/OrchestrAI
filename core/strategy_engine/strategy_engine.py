# Summary: Implements strategy engine logic for the OrchestrAI runtime.
from pathlib import Path
import yaml

ROLE_CAPABILITY_MAP = {
    "scriptwriter": "content",
    "media": "media",
    "publisher": "publishing",
    "strategist": "publishing",
    "analytics": "analytics",
}

class StrategyEngine:

    def apply_strategy(self, intent_step, runtime_entity: dict):
        intent_data = intent_step.to_dict()
        workflow_profile = runtime_entity.get("workflow_profile", {}) or {}

        pack_id = runtime_entity.get("strategy_pack")
        pack = {}

        if pack_id:
            pack = self._load_strategy_pack(pack_id)
            intent_modifiers = pack.get("intent_modifiers", {})

            # Inject model_policy from YAML
            intent_data["model_policy"] = self._pack_value(
                pack,
                intent_modifiers,
                "model_policy",
                {},
            )

            restricted_capabilities = self._pack_value(
                pack,
                intent_modifiers,
                "restricted_capabilities",
            )
            if restricted_capabilities is not None:
                intent_data["restricted_capabilities"] = restricted_capabilities

            allowed_actions = self._pack_value(
                pack,
                intent_modifiers,
                "allowed_actions",
            )
            if allowed_actions is not None:
                intent_data["allowed_actions"] = allowed_actions

            autonomy = self._pack_value(
                pack,
                intent_modifiers,
                "autonomy",
            )
            if autonomy is not None:
                intent_data["autonomy"] = autonomy

            pack_workflow_defaults = pack.get("workflow_profile_defaults", {}) or {}
            analytics_feedback = workflow_profile.get(
                "analytics_feedback",
                pack_workflow_defaults.get("analytics_feedback"),
            )
            intent_data["analytics_enabled"] = analytics_feedback == "enabled"

        intent_data["capability_map"] = ROLE_CAPABILITY_MAP

        return intent_step.__class__(intent_data)

    def inject_execution_posture(self, context, strategized_plan):
        plan_data = (
            strategized_plan.to_dict()
            if hasattr(strategized_plan, "to_dict")
            else strategized_plan or {}
        )

        posture = {
            "restricted_capabilities": plan_data.get("restricted_capabilities", []),
            "allowed_actions": plan_data.get("allowed_actions", []),
            "autonomy": plan_data.get("autonomy"),
            "model_policy": plan_data.get("model_policy", {}),
        }

        context.set_posture(posture)
        return posture

    def _load_strategy_pack(self, pack_id: str):
        base_path = Path("presets/strategy_packs")
        pack_file = base_path / f"{pack_id}.yaml"

        if not pack_file.exists():
            raise FileNotFoundError(f"Strategy pack not found: {pack_file}")

        with open(pack_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _pack_value(self, pack: dict, intent_modifiers: dict, key: str, default=None):
        if key in pack:
            return pack[key]
        if isinstance(intent_modifiers, dict) and key in intent_modifiers:
            return intent_modifiers[key]
        return default