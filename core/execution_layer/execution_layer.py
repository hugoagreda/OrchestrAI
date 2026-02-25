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

        print(f"[RUNTIME STEP] capability={step.capability} | action={step.action}")
        
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

        # -------------------------------------------------
        # 🔥 OS-native capability resolution
        # -------------------------------------------------

        if step.capability and step.action:
            key = f"{step.capability}.{step.action}"
            handler = self._step_registry.get(key)

            if handler:
                return handler

        # -------------------------------------------------
        # 🔥 Fallback: action-only (backward compatibility)
        # -------------------------------------------------

        if step.action:
            return self._step_registry.get(step.action)

        return None


    def _is_step_allowed(self, step: RuntimeStep) -> bool:

        behavior = self.context._state.get("behavior", {})
    
        allowed = behavior.get("allowed_actions", [])
        restricted = behavior.get("restricted_actions", [])
    
        step_action = step.action
    
        # -------------------------------------------------
        # Restriction check
        # -------------------------------------------------
        if step_action in restricted:
            print(f"[BLOCKED] Step restricted by behavior: {step_action}")
            return False
    
        # -------------------------------------------------
        # Allowed whitelist
        # -------------------------------------------------
        if allowed and step_action not in allowed:
            print(f"[SKIPPED] Step not in allowed_actions: {step_action}")
            return False
    
        return True
    
    # =====================================================
    # Step Lifecycle Runner
    # =====================================================
    def _run_step(self, handler, step: RuntimeStep):

        # 🔥 Runtime awareness (execution position)
        self.context.set_runtime("current_step", {
            "capability": step.capability,
            "action": step.action,
        })

        # Lifecycle start
        self.context._log_event("STEP_STARTED", {
            "capability": step.capability,
            "action": step.action,
        })

        # Execute capability
        handler(self.context)

        # Lifecycle end
        self.context._log_event("STEP_FINISHED", {
            "capability": step.capability,
            "action": step.action,
        })