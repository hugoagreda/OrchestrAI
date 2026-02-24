# Dynamic executor with auto-discovered actions
# Capability-aware dispatcher with structured lifecycle.

from core.execution_layer.execution_context import ExecutionContext
from core.action.action_registry import discover_actions
from core.execution_layer.runtime_step import RuntimeStep


class ExecutionLayer:

    def __init__(self):
        # 🔥 Dynamic capability registry
        self._step_registry = discover_actions()
        self.context: ExecutionContext | None = None

    # =====================================================
    # Execute Workflow
    # =====================================================
    def execute(self, workflow: dict, context: ExecutionContext):

        # Context viene desde fuera → SSOT real
        self.context = context

        steps = workflow.get("steps", [])

        print("\n--- EXECUTION START ---")

        # 🔥 Convertimos dict → RuntimeStep (contrato interno)
        for step_data in steps:
            step = RuntimeStep(step_data)
            self._execute_step(step)

        print("\n--- FINAL CONTEXT STATE ---")
        print(self.context.dump())

        print("\n--- EXECUTION END ---")

    # =====================================================
    # Step Orchestrator
    # =====================================================
    def _execute_step(self, step: RuntimeStep):

        handler = self._resolve_handler(step)

        if not handler:
            print(f"[UNKNOWN STEP] {step.name}")
            return

        if not self._is_step_allowed(step):
            return
        
        self._run_step(handler, step)

    # =====================================================
    # Capability Resolver
    # =====================================================
    def _resolve_handler(self, step: RuntimeStep):

        handler = None

        # 1️⃣ capability explícita
        if step.capability_key():
            handler = self._step_registry.get(step.capability_key())

        # 2️⃣ role + name namespace
        if not handler and step.namespaced_key():
            handler = self._step_registry.get(step.namespaced_key())

        # 3️⃣ fallback legacy
        if not handler and step.legacy_key():
            handler = self._step_registry.get(step.legacy_key())

        return handler


    def _is_step_allowed(self, step: RuntimeStep) -> bool:

        behavior = self.context._state.get("behavior", {})

        allowed = behavior.get("allowed_actions", [])
        restricted = behavior.get("restricted_actions", [])

        step_name = step.name

        if step_name in restricted:
            print(f"[BLOCKED] Step restricted by behavior: {step_name}")
            return False

        if allowed and step_name not in allowed:
            print(f"[SKIPPED] Step not in allowed_actions: {step_name}")
            return False

        return True
    
    # =====================================================
    # Step Lifecycle Runner
    # =====================================================
    def _run_step(self, handler, step: RuntimeStep):

        step_name = step.name
        step_role = step.role

        # 🔥 Runtime awareness (execution position)
        self.context.set_runtime("current_step", step.to_dict())

        # Lifecycle start
        self.context._log_event("STEP_STARTED", {
            "step": step_name,
            "role": step_role
        })

        # Execute capability
        handler(self.context)

        # Lifecycle end
        self.context._log_event("STEP_FINISHED", {
            "step": step_name,
            "role": step_role
        })