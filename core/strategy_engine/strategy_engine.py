from pathlib import Path
import yaml


class StrategyEngine:

    def apply_strategy(self, intent_step, runtime_entity: dict):

        intent_data = intent_step.to_dict()

        # -------------------------------------------------
        # 1️⃣ Strategy Pack (Entity OS Profile)
        # -------------------------------------------------
        pack_id = runtime_entity.get("strategy_pack")

        pack = {}

        if pack_id:

            pack = self._load_strategy_pack(pack_id)

            modifiers = pack.get("intent_modifiers", {})

            # merge intent modifiers
            for key, value in modifiers.items():

                if isinstance(value, list):
                    existing = intent_data.get(key, [])
                    intent_data[key] = list(set(existing + value))
                else:
                    intent_data[key] = value

        # -------------------------------------------------
        # 2️⃣ Workflow Profile Defaults (NEW — OS posture)
        # -------------------------------------------------
        pack_workflow_defaults = pack.get("workflow_profile_defaults", {})
        entity_workflow_profile = runtime_entity.get("workflow_profile", {})

        # Strategy pack define defaults,
        # entidad puede overridear
        merged_workflow_profile = {
            **pack_workflow_defaults,
            **entity_workflow_profile
        }

        intent_data["workflow_profile"] = merged_workflow_profile

        # -------------------------------------------------
        # 3️⃣ Workflow Profile Runtime Flags (existing logic)
        # -------------------------------------------------
        workflow_profile = merged_workflow_profile

        if workflow_profile.get("media_generation") == "disabled":

            restricted_caps = intent_data.get("restricted_capabilities", [])
            restricted_caps.append("media.*")
            intent_data["restricted_capabilities"] = restricted_caps

        if workflow_profile.get("publishing") == "optional":
            intent_data["publishing_optional"] = True

        if workflow_profile.get("analytics_feedback") == "enabled":
            intent_data["analytics_enabled"] = True

        return intent_step.__class__(intent_data)

    # -------------------------------------------------
    # Strategy Pack Loader
    # -------------------------------------------------
    def _load_strategy_pack(self, pack_id: str):

        base_path = Path("presets/strategy_packs")
        pack_file = base_path / f"{pack_id}.yaml"

        if not pack_file.exists():
            raise FileNotFoundError(f"Strategy pack not found: {pack_file}")

        with open(pack_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)