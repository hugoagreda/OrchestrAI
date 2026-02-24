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
    # Resolve Strategy (Intent Translator)
    # -------------------------------------------------
    def _resolve_strategy(self, intent: dict) -> str:

        content_type = intent.get("content_type", "generic")

        strategy_map = {
            "short_video": "short_video",
            "generic": "generic",
        }

        return strategy_map.get(content_type, "generic")

    # -------------------------------------------------
    # Resolve Strategy Profile
    # -------------------------------------------------
    def _resolve_profile(self, intent: dict) -> str:

        autonomy = intent.get("autonomy", "medium")

        if autonomy == "low":
            return "low_autonomy"

        return "default"

    # -------------------------------------------------
    # Build Workflow
    # -------------------------------------------------
    def build_workflow(self, intent: dict) -> dict:

        # 🔥 Intent → Strategy
        strategy_id = self._resolve_strategy(intent)

        workflow_data = self._load_workflow(strategy_id)

        profile = self._resolve_profile(intent)

        # -------------------------------------------------
        # Strategy Profile selection
        # -------------------------------------------------
        if "strategies" in workflow_data:
            workflow = dict(
                workflow_data["strategies"].get(profile)
                or workflow_data["strategies"]["default"]
            )
        else:
            workflow = dict(workflow_data)

        # -------------------------------------------------
        # 🔥 Behavior-aware step filtering (PRE-RUNTIME)
        # -------------------------------------------------
        allowed = intent.get("allowed_actions", [])
        restricted = intent.get("restricted_actions", [])
        restricted_caps = intent.get("restricted_capabilities", [])

        if "steps" in workflow:

            filtered_steps = []

            for step in workflow["steps"]:
                step_name = step.get("name")
                step_role = step.get("role")

                capability = f"{step_role}.{step_name}" if step_role else step_name
            
                # Skip restricted
                if step_name in restricted:
                    continue

                # If allowed list exists → must be inside
                if allowed and step_name not in allowed:
                    continue

                blocked = False
                for rule in restricted_caps:
                    if capability.endswith("*"):
                        if capability.startswith(rule[:-2]):
                            blocked = True
                            break

                    elif rule == capability:
                        blocked = True
                        break

                if blocked:
                    continue

                filtered_steps.append(step)

            workflow["steps"] = filtered_steps

        # -------------------------------------------------
        # Inject Intent Metadata (non-destructive)
        # -------------------------------------------------
        if intent.get("platform"):
            workflow["platform"] = intent["platform"]

        if intent.get("autonomy"):
            workflow["autonomy"] = intent["autonomy"]

        return workflow