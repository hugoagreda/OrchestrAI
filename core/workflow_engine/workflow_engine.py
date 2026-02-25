from pathlib import Path
import yaml


class WorkflowEngine:

    def __init__(self, workflows_path="presets/workflows"):
        self.workflows_path = Path(workflows_path)

    # -------------------------------------------------
    # Load Workflow Preset
    # -------------------------------------------------
    def _load_workflow(self, workflow_id: str) -> dict:

        workflow_file = self.workflows_path / f"{workflow_id}.yaml"

        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_file}")

        with open(workflow_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # -------------------------------------------------
    # Build Workflow (PURE TRANSLATOR)
    # -------------------------------------------------
    def build_workflow(self, intent: dict) -> dict:

        workflow_id = intent.get("content_type", "generic")

        workflow_data = self._load_workflow(workflow_id)

        allowed = intent.get("allowed_actions", [])
        restricted = intent.get("restricted_actions", [])
        restricted_caps = intent.get("restricted_capabilities", [])
        capability_map = intent.get("capability_map", {})

        profile = "default"

        if "strategies" in workflow_data:
            workflow = dict(workflow_data["strategies"][profile])
        else:
            workflow = dict(workflow_data)

        filtered_steps = []

        if "steps" in workflow:

            for step in workflow["steps"]:

                # -----------------------------------------
                # 🔥 Normalize to OS-native schema
                # -----------------------------------------
                action = step.get("action") or step.get("name")
                role = step.get("role")

                if not action:
                    continue

                capability = step.get("capability")

                # Strategy capability mapping
                if not capability and role and role in capability_map:
                    capability = capability_map[role]

                # Infer fallback capability
                if not capability:
                    action_to_capability = {
                        "generate_script": "content",
                        "prepare_publish": "publishing",
                        "generate_media": "media",
                        "collect_metrics": "analytics",
                    }
                    capability = action_to_capability.get(action)

                # -----------------------------------------
                # Filtering rules
                # -----------------------------------------
                if action in restricted:
                    continue

                if allowed and action not in allowed:
                    continue

                full_capability = f"{capability}.{action}" if capability else action

                blocked = False

                for rule in restricted_caps:

                    if rule.endswith("*"):
                        namespace = rule[:-2]
                        if full_capability.startswith(namespace):
                            blocked = True
                            break

                    elif rule == full_capability:
                        blocked = True
                        break

                if blocked:
                    continue

                # -----------------------------------------
                # ABI Step (FINAL SHAPE)
                # -----------------------------------------
                normalized_step = {
                    "capability": capability,
                    "action": action,
                }

                filtered_steps.append(normalized_step)

        workflow["steps"] = filtered_steps

        # Inject metadata (NON-DESTRUCTIVE)
        if intent.get("platform"):
            workflow["platform"] = intent["platform"]

        if intent.get("autonomy"):
            workflow["autonomy"] = intent["autonomy"]

        if intent.get("analytics_enabled"):
            workflow["analytics_enabled"] = True

        return workflow