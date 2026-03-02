from core.execution_layer.execution_context import ExecutionContext
from core.execution_layer.runtime_step import RuntimeStep
import time

class ExecutionLayer:
    def __init__(self, kernel):
        # La Layer recibe el Kernel ya configurado (Inyección de dependencias)
        self.kernel = kernel
        self.context: ExecutionContext | None = None
        self.model_decisions = []

    def log_model_decision(self, decision: dict):
        self.model_decisions.append(decision)

    def execute(self, workflow: dict, context: ExecutionContext, enable_profiling: bool = False):

        self.context = context
        steps = workflow.get("steps", [])
        pipeline_start = time.perf_counter()
        self.context.start_pipeline(len(steps), profiling_enabled=enable_profiling)

        print("\n--- [OS] EXECUTION PIPELINE START ---")

        for step_data in steps:
            step = RuntimeStep(step_data)
            self._execute_step_step_lifecycle(step)

        if enable_profiling:
            pipeline_duration_ms = (time.perf_counter() - pipeline_start) * 1000
            self.context.set_pipeline_profile(pipeline_duration_ms)
            self.context.set_kernel_cache_metrics(self.kernel.cache_stats())

        self.context.finish_pipeline()
        print("\n--- [OS] EXECUTION PIPELINE END ---")

    async def execute_async(self, workflow: dict, context: ExecutionContext, enable_profiling: bool = False):
        self.context = context
        steps = workflow.get("steps", [])
        pipeline_start = time.perf_counter()
        self.context.start_pipeline(len(steps), profiling_enabled=enable_profiling)

        print("\n--- [OS] EXECUTION PIPELINE START ---")

        for step_data in steps:
            step = RuntimeStep(step_data)
            await self._execute_step_step_lifecycle_async(step)

        if enable_profiling:
            pipeline_duration_ms = (time.perf_counter() - pipeline_start) * 1000
            self.context.set_pipeline_profile(pipeline_duration_ms)
            self.context.set_kernel_cache_metrics(self.kernel.cache_stats())

        self.context.finish_pipeline()
        print("\n--- [OS] EXECUTION PIPELINE END ---")

    def _posture_block_reason(self, step: RuntimeStep) -> str | None:
        posture = self.context.get_posture()
    
        restricted = posture.get("restricted_capabilities", [])
        allowed = posture.get("allowed_actions", [])
    
        for namespace in restricted:
            prefix = namespace.replace(".*", "")
            if step.capability and step.capability.startswith(prefix):
                return f"Capability '{step.capability}' restricted by posture"
    
        if allowed and step.action not in allowed:
            return f"Action '{step.action}' not allowed by posture"
    
        return None

    def _execute_step_step_lifecycle(self, step: RuntimeStep):
        step_start = time.perf_counter()

        # 1. Preparación de Contexto
        self.context.set_runtime("current_step", step.to_dict())
        
        # 2. Telemetría de Inicio
        self.context._log_event("STEP_STARTED", {
            "capability": step.capability,
            "action": step.action
        })

        print(f"[RUNTIME STEP] capability={step.capability} | action={step.action}")
        print(f"[RUNTIME] Calling Kernel -> {step.capability_key() or step.action}")

        block_reason = self._posture_block_reason(step)
        if block_reason:
            duration_ms = (time.perf_counter() - step_start) * 1000
            self.context._log_event("STEP_BLOCKED_BY_POSTURE", {
                "capability": step.capability,
                "action": step.action,
                "reason": block_reason,
            })
            self.context.record_step_failure(
                step.capability or "unknown",
                step.action or "unknown",
                duration_ms,
                block_reason
            )
            print(f"[RUNTIME BLOCKED] {block_reason}")
            self.context._log_event("STEP_FINISHED", {"action": step.action})
            return
        
        # 3. Transferencia de Control al Kernel (Ring 0)
        try:
            self.kernel.execute(step, self.context)
        except Exception as e:
            duration_ms = (time.perf_counter() - step_start) * 1000
            self.context._log_event("STEP_CRITICAL_FAILURE", {"error": str(e)})
            self.context.record_step_failure(
                step.capability or "unknown",
                step.action or "unknown",
                duration_ms,
                str(e)
            )
            print(f"[RUNTIME ERROR] {e}")
        else:
            duration_ms = (time.perf_counter() - step_start) * 1000
            self.context.record_step_success(
                step.capability or "unknown",
                step.action or "unknown",
                duration_ms
            )

        # 4. Telemetría de Cierre
        self.context._log_event("STEP_FINISHED", {"action": step.action})

    async def _execute_step_step_lifecycle_async(self, step: RuntimeStep):
        step_start = time.perf_counter()

        self.context.set_runtime("current_step", step.to_dict())
        self.context._log_event("STEP_STARTED", {
            "capability": step.capability,
            "action": step.action
        })

        print(f"[RUNTIME STEP] capability={step.capability} | action={step.action}")
        print(f"[RUNTIME] Calling Kernel -> {step.capability_key() or step.action}")

        block_reason = self._posture_block_reason(step)
        if block_reason:
            duration_ms = (time.perf_counter() - step_start) * 1000
            self.context._log_event("STEP_BLOCKED_BY_POSTURE", {
                "capability": step.capability,
                "action": step.action,
                "reason": block_reason,
            })
            self.context.record_step_failure(
                step.capability or "unknown",
                step.action or "unknown",
                duration_ms,
                block_reason
            )
            print(f"[RUNTIME BLOCKED] {block_reason}")
            self.context._log_event("STEP_FINISHED", {"action": step.action})
            return

        try:
            await self.kernel.execute_async(step, self.context)
        except Exception as e:
            duration_ms = (time.perf_counter() - step_start) * 1000
            self.context._log_event("STEP_CRITICAL_FAILURE", {"error": str(e)})
            self.context.record_step_failure(
                step.capability or "unknown",
                step.action or "unknown",
                duration_ms,
                str(e)
            )
            print(f"[RUNTIME ERROR] {e}")
        else:
            duration_ms = (time.perf_counter() - step_start) * 1000
            self.context.record_step_success(
                step.capability or "unknown",
                step.action or "unknown",
                duration_ms
            )

        self.context._log_event("STEP_FINISHED", {"action": step.action})