# Dynamic executor with auto-discovered actions
# Capability-aware dispatcher with structured lifecycle.

from core.execution_layer.execution_context import ExecutionContext
from core.action.action_registry import discover_actions
from core.execution_layer.runtime_step import RuntimeStep
from core.action.capability_kernel import CapabilityKernel

class ExecutionLayer:

    def __init__(self):
        # Dynamic capability registry
        self._step_registry = discover_actions()
        self.kernel = CapabilityKernel(self._step_registry)
        self.context: ExecutionContext | None = None

    # =====================================================
    # Execute Workflow
    # =====================================================
    def execute(self, workflow: dict, context: ExecutionContext):

        # Context viene desde fuera → SSOT real
        self.context = context

        steps = workflow.get("steps", [])

        print("\n--- EXECUTION START ---")

        # dict → RuntimeStep ABI
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
            print(f"[UNKNOWN STEP] {step.action}")
            return

        self._run_step(handler, step)

    # =====================================================
    # Capability Resolver (PURE OS)
    # =====================================================
    def _resolve_handler(self, step: RuntimeStep):

        handler = None

        # 1️⃣ capability.action (OS native)
        if step.capability_key():
            handler = self._step_registry.get(step.capability_key())

        # 2️⃣ fallback → action only
        if not handler and step.legacy_key():
            handler = self._step_registry.get(step.legacy_key())

        return handler

    # =====================================================
    # Step Lifecycle Runner
    # =====================================================
    def _run_step(self, handler, step: RuntimeStep):

        # Runtime awareness
        self.context.set_runtime("current_step", step.to_dict())

        # Lifecycle start
        self.context._log_event("STEP_STARTED", {
            "capability": step.capability,
            "action": step.action
        })

        # Execute capability
        self.kernel.execute(step, self.context)

        # Lifecycle end
        self.context._log_event("STEP_FINISHED", {
            "capability": step.capability,
            "action": step.action
        })