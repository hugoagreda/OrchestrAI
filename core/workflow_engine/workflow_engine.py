from pathlib import Path
import yaml


class WorkflowEngine:

    def __init__(self, workflows_path="presets/workflows"):
        self.workflows_path = Path(workflows_path)

    # -------------------------
    # Load Workflow Preset
    # -------------------------
    def _load_workflow(self, workflow_id: str) -> dict:
        workflow_file = self.workflows_path / f"{workflow_id}.yaml"

        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_file}")

        with open(workflow_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # -------------------------
    # Build Workflow
    # -------------------------
    def build_workflow(self, action_plan: dict) -> dict:

        content_type = action_plan.get("content_type", "generic")

        workflow = self._load_workflow(content_type)

        # Optional override from planner
        if action_plan.get("platform"):
            workflow["platform"] = action_plan["platform"]

        return workflow