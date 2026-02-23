# Dynamic executor with auto-discovered actions
# and role-ready dispatch structure.

from core.execution_layer.execution_context import ExecutionContext
from core.action.action_registry import discover_actions


class ExecutionLayer:

    def __init__(self, context=None):
        self.context = context or ExecutionContext()

        self._step_registry = discover_actions()

    # =====================================================
    # Execute Workflow
    # =====================================================

    def execute(self, workflow: dict):

        steps = workflow.get("steps", [])

        print("\n--- EXECUTION START ---")

        for step in steps:
            self._execute_step(step)

        print("\n--- FINAL CONTEXT STATE ---")
        print(self.context.dump())

        print("\n--- EXECUTION END ---")

    # =====================================================
    # Step Dispatcher
    # =====================================================

    def _execute_step(self, step: dict):

        step_name = step.get("name")
        step_role = step.get("role")

        # -------------------------------------------------
        # 🔥 FUTURE READY: role-first resolution (safe)
        # -------------------------------------------------
        handler = None

        # (por ahora solo usamos name, pero ya queda preparado)
        if step_name:
            handler = self._step_registry.get(step_name)

        if not handler:
            print(f"[UNKNOWN STEP] {step_name}")
            return

        # -------------------------------------------------
        # Execution lifecycle
        # -------------------------------------------------
        self.context._log_event("STEP_STARTED", {
            "step": step_name,
            "role": step_role
        })

        handler(self.context)

        self.context._log_event("STEP_FINISHED", {
            "step": step_name,
            "role": step_role
        })