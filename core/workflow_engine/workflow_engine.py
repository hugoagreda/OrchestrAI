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
    # Build Workflow (PURE STRUCTURAL TRANSLATOR)
    # -------------------------------------------------
    def build_workflow(self, intent: dict) -> dict:

        workflow_id = intent.get("content_type", "generic")
        workflow_data = self._load_workflow(workflow_id)

        profile = "default"

        # Strategy profiles supported structurally
        if "strategies" in workflow_data:
            workflow = dict(workflow_data["strategies"][profile])
        else:
            workflow = dict(workflow_data)

        normalized_steps = []

        # -------------------------------------------------
        # 🔥 WORKFLOW PROFILE (STRUCTURAL ONLY)
        # -------------------------------------------------
        workflow_profile = intent.get("workflow_profile", {})

        media_enabled = workflow_profile.get("media_generation", "enabled") != "disabled"
        publishing_mode = workflow_profile.get("publishing", "enabled")
        analytics_enabled = workflow_profile.get("analytics_feedback", False)

        # -------------------------------------------------
        # 🔥 ABI NORMALIZATION + STRUCTURAL FILTER
        # -------------------------------------------------
        if "steps" in workflow:

            for step in workflow["steps"]:
                action = step.get("action") or step.get("name")
                role = step.get("role")

                # ------------------------------------------
                # STRUCTURAL FILTER (NOT POLICY ENFORCEMENT)
                # ------------------------------------------
                if role == "media" and not media_enabled:
                    continue

                if role == "strategist" and publishing_mode == "disabled":
                    continue

                if role == "analytics" and not analytics_enabled:
                    continue

                capability_map = intent.get("capability_map", {})
                namespace = capability_map.get(role, "unknown")

                normalized_step = {
                    "capability": namespace,
                    "action": action,
                    "payload": step.get("payload", {}),
                    "metadata": {
                        "role": role,
                        "original_intent": intent.get("query")
                    }
                }

                normalized_steps.append(normalized_step)

        workflow["steps"] = normalized_steps

        # -------------------------------------------------
        # Metadata Injection (NON-DESTRUCTIVE)
        # -------------------------------------------------
        if intent.get("platform"):
            workflow["platform"] = intent["platform"]

        if intent.get("autonomy"):
            workflow["autonomy"] = intent["autonomy"]

        if intent.get("analytics_enabled"):
            workflow["analytics_enabled"] = True

        return workflow