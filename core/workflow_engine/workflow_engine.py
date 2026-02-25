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
    # Build Workflow (OS Translator)
    # -------------------------------------------------
    
    def build_workflow(self, intent: dict) -> dict:

        # -------------------------------------------------
        # 🔥 Strategy already resolved by StrategyEngine
        # -------------------------------------------------
        workflow_id = intent.get("content_type", "generic")

        workflow_data = self._load_workflow(workflow_id)

        workflow_profile = intent.get("workflow_profile", {})

        # -------------------------------------------------
        # Strategy Profile selection (pure translation)
        # -------------------------------------------------
        profile = intent.get("workflow_profile", {}).get("profile", "default")

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

                # -------------------------------------------------
                # 🔥 Normalize FIRST (OS schema)
                # -------------------------------------------------
                if "name" in step:
                    step["action"] = step.pop("name")

                role = step.pop("role", None)

                # -------------------------------------------------
                # 🔥 Inject capability from Strategy
                # -------------------------------------------------
                capability_map = intent.get("capability_map", {})

                if role and role in capability_map:
                    step["capability"] = capability_map[role]

                # -------------------------------------------------
                # 🔥 Infer capability from action if missing
                # -------------------------------------------------
                if not step.get("capability"):
                
                    action_to_capability = {
                        "generate_script": "content",
                        "prepare_publish": "publishing",
                        "generate_media": "media",
                        "collect_metrics": "analytics",
                    }

                    inferred = action_to_capability.get(step.get("action"))
                    if inferred:
                        step["capability"] = inferred

                # -------------------------------------------------
                # Filtering
                # -------------------------------------------------
                step_action = step.get("action")
                step_capability = step.get("capability")

                capability = (
                    f"{step_capability}.{step_action}"
                    if step_capability else step_action
                )

                if step_action in restricted:
                    continue
                
                if allowed and step_action not in allowed:
                    continue
                
                blocked = False
                for rule in restricted_caps:
                
                    if rule.endswith("*"):
                        namespace = rule[:-2]
                        if capability.startswith(namespace):
                            blocked = True
                            break
                        
                    elif rule == capability:
                        blocked = True
                        break
                    
                if blocked:
                    continue
                
                filtered_steps.append(step)
            # 🔥 mover esto fuera del for
            workflow["steps"] = filtered_steps

        # -------------------------------------------------
        # 🔥 Strategy Workflow Posture (Entity OS Layer)
        # -------------------------------------------------
        if workflow_profile:

            if workflow_profile.get("publishing") == "optional":

                if "steps" in workflow:
                    workflow["steps"] = [
                        step for step in workflow["steps"]
                        if step.get("name") != "prepare_publish"
                    ]

            if workflow_profile.get("analytics_feedback") == "enabled":
                workflow["analytics_enabled"] = True

        # -------------------------------------------------
        # Inject Intent Metadata (non-destructive)
        # -------------------------------------------------
        if intent.get("platform"):
            workflow["platform"] = intent["platform"]

        if intent.get("autonomy"):
            workflow["autonomy"] = intent["autonomy"]

        return workflow
    