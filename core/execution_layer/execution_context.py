# Summary: Implements execution context logic for the OrchestrAI runtime.
class ExecutionContext:
    """
    Contenedor de Estado del Kernel.

    Responsabilidades:
        - Hidratación de identidad
        - Restricciones de comportamiento
        - Memoria de capacidades (datos de runtime)
        - Almacenamiento de artefactos
        - Eventos de ciclo de vida
    """

    def __init__(self):

        # -------------------------
        # ESTADO BASE (nativo del sistema)
        # -------------------------
        self._state = {
            "identity": {},
            "behavior": {},
            "memory": {},     # 🔥 antes "execution"
            "artifacts": {},
            "runtime": {},
            "model_decisions": [],
            "execution_traces": [],
            "metrics": {
                "total_steps": 0,
                "successful_steps": 0,
                "failed_steps": 0,
                "step_durations_ms": [],
                "capability_invocations": {},
                "last_error": None,
                "profiling": {
                    "enabled": False,
                    "pipeline_duration_ms": 0.0,
                    "avg_step_duration_ms": 0.0,
                    "slowest_step": None,
                },
                "kernel_cache": {
                    "hits": 0,
                    "misses": 0,
                    "size": 0,
                },
            }
        }

        # -------------------------
        # REGISTRO DE EVENTOS
        # -------------------------
        self._events = []

    # =====================================================
    # HIDRATACIÓN
    # =====================================================

    def load_identity(self, identity_data: dict):
        self._state["identity"] = identity_data or {}
        self._log_event("IDENTITY_LOADED", {})

    def load_behavior(self, behavior_data: dict):
        self._state["behavior"] = behavior_data or {}
        self._log_event("BEHAVIOR_LOADED", {})

    def set_posture(self, posture: dict):
        posture = posture or {}
        self._state["runtime"]["posture"] = posture
        self._state["runtime"]["execution_posture"] = posture

    def get_posture(self) -> dict:
        runtime = self._state["runtime"]

        if "posture" in runtime:
            return runtime["posture"]
        
        return runtime.get("execution_posture", {})
    
    # =====================================================
    # MEMORIA (salidas de capacidades)
    # =====================================================

    def set(self, key, value):
        """
        Escritura de memoria nativa.
        Las capacidades guardan aquí sus salidas de runtime.
        """
        self._state["memory"][key] = value
        self._log_event("STATE_UPDATED", {key: value})

    def get(self, key, default=None):
        return self._state["memory"].get(key, default)

    # =====================================================
    # RUNTIME (interno del kernel)
    # =====================================================

    def set_runtime(self, key, value):
        self._state["runtime"][key] = value

    def get_runtime(self, key, default=None):
        return self._state["runtime"].get(key, default)

    def set_budget(self, total_budget: float):
        total = float(total_budget)
        self._state["runtime"]["budget"] = {
            "total": total,
            "remaining": total,
            "spent": 0.0,
        }

    def get_budget(self) -> dict | None:
        budget = self._state["runtime"].get("budget")
        if isinstance(budget, dict):
            return dict(budget)
        return None

    def consume_budget(self, amount: float):
        budget = self._state["runtime"].get("budget")
        if not isinstance(budget, dict):
            return

        spend = max(float(amount), 0.0)
        budget["spent"] = float(budget.get("spent", 0.0)) + spend
        remaining = float(budget.get("remaining", 0.0)) - spend
        budget["remaining"] = max(remaining, 0.0)

    def log_model_decision(self, decision: dict):
        self._state["model_decisions"].append(decision or {})
        self._log_event("MODEL_DECISION_LOGGED", {"decision": decision or {}})

    def model_decisions(self):
        return list(self._state["model_decisions"])

    def log_execution_trace(self, trace: dict):
        payload = trace or {}
        self._state["execution_traces"].append(payload)
        self._log_event("EXECUTION_TRACE_LOGGED", {"trace": payload})

    def execution_traces(self):
        return list(self._state["execution_traces"])

    # =====================================================
    # MÉTRICAS
    # =====================================================

    def start_pipeline(self, total_steps: int, profiling_enabled: bool = False):
        metrics = self._state["metrics"]
        self._state["execution_traces"] = []
        metrics["total_steps"] = total_steps
        metrics["successful_steps"] = 0
        metrics["failed_steps"] = 0
        metrics["step_durations_ms"] = []
        metrics["capability_invocations"] = {}
        metrics["last_error"] = None
        metrics["profiling"] = {
            "enabled": profiling_enabled,
            "pipeline_duration_ms": 0.0,
            "avg_step_duration_ms": 0.0,
            "slowest_step": None,
        }
        metrics["kernel_cache"] = {
            "hits": 0,
            "misses": 0,
            "size": 0,
        }
        self._log_event("PIPELINE_STARTED", {
            "total_steps": total_steps,
            "profiling_enabled": profiling_enabled,
        })

    def record_step_success(self, capability: str, action: str, duration_ms: float):
        metrics = self._state["metrics"]
        metrics["successful_steps"] += 1
        metrics["step_durations_ms"].append({
            "capability": capability,
            "action": action,
            "status": "success",
            "duration_ms": round(duration_ms, 3),
        })
        metrics["capability_invocations"][capability] = (
            metrics["capability_invocations"].get(capability, 0) + 1
        )

    def record_step_failure(self, capability: str, action: str, duration_ms: float, error: str):
        metrics = self._state["metrics"]
        metrics["failed_steps"] += 1
        metrics["last_error"] = error
        metrics["step_durations_ms"].append({
            "capability": capability,
            "action": action,
            "status": "failed",
            "duration_ms": round(duration_ms, 3),
            "error": error,
        })
        metrics["capability_invocations"][capability] = (
            metrics["capability_invocations"].get(capability, 0) + 1
        )

    def finish_pipeline(self):
        metrics = self._state["metrics"]
        self._log_event("PIPELINE_FINISHED", {
            "total_steps": metrics["total_steps"],
            "successful_steps": metrics["successful_steps"],
            "failed_steps": metrics["failed_steps"],
        })

    def set_pipeline_profile(self, pipeline_duration_ms: float):
        metrics = self._state["metrics"]
        durations = metrics.get("step_durations_ms", [])

        slowest_step = None
        if durations:
            slowest_step = max(durations, key=lambda item: item.get("duration_ms", 0.0))

        avg_duration = 0.0
        if durations:
            total = sum(item.get("duration_ms", 0.0) for item in durations)
            avg_duration = round(total / len(durations), 3)

        metrics["profiling"] = {
            "enabled": True,
            "pipeline_duration_ms": round(pipeline_duration_ms, 3),
            "avg_step_duration_ms": avg_duration,
            "slowest_step": slowest_step,
        }

    def set_kernel_cache_metrics(self, cache_metrics: dict):
        metrics = self._state["metrics"]
        metrics["kernel_cache"] = {
            "hits": int(cache_metrics.get("hits", 0)),
            "misses": int(cache_metrics.get("misses", 0)),
            "size": int(cache_metrics.get("size", 0)),
        }

    def metrics(self):
        return dict(self._state["metrics"])

    # =====================================================
    # ARTEFACTOS
    # =====================================================

    def store_artifact(self, name, value):
        self._state["artifacts"][name] = value
        self._log_event("ARTIFACT_STORED", {"name": name})

    def get_artifact(self, name, default=None):
        return self._state["artifacts"].get(name, default)

    # =====================================================
    # EVENTOS
    # =====================================================

    def _log_event(self, event_type, payload=None):
        self._events.append({
            "type": event_type,
            "payload": payload or {}
        })

    def events(self):
        return list(self._events)

    # =====================================================
    # DEPURACIÓN
    # =====================================================

    def dump(self):
        return {
            "state": self._state,
            "events": self._events
        }