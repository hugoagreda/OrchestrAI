class ExecutionContext:
    """
    Kernel State Container.

    Responsibilities:
        - Identity hydration
        - Behavior constraints
        - Capability memory (runtime data)
        - Artifact storage
        - Lifecycle events
    """

    def __init__(self):

        # -------------------------
        # CORE STATE (OS-native)
        # -------------------------
        self._state = {
            "identity": {},
            "behavior": {},
            "memory": {},     # 🔥 antes "execution"
            "artifacts": {},
            "runtime": {}
        }

        # -------------------------
        # EVENT LOG
        # -------------------------
        self._events = []

    # =====================================================
    # HYDRATION
    # =====================================================

    def load_identity(self, identity_data: dict):
        self._state["identity"] = identity_data or {}
        self._log_event("IDENTITY_LOADED", {})

    def load_behavior(self, behavior_data: dict):
        self._state["behavior"] = behavior_data or {}
        self._log_event("BEHAVIOR_LOADED", {})

    # =====================================================
    # MEMORY (capability outputs)
    # =====================================================

    def set(self, key, value):
        """
        OS-native memory write.
        Capabilities store runtime outputs here.
        """
        self._state["memory"][key] = value
        self._log_event("STATE_UPDATED", {key: value})

    def get(self, key, default=None):
        return self._state["memory"].get(key, default)

    # =====================================================
    # RUNTIME (kernel internal)
    # =====================================================

    def set_runtime(self, key, value):
        self._state["runtime"][key] = value

    def get_runtime(self, key, default=None):
        return self._state["runtime"].get(key, default)

    # =====================================================
    # ARTIFACTS
    # =====================================================

    def store_artifact(self, name, value):
        self._state["artifacts"][name] = value
        self._log_event("ARTIFACT_STORED", {"name": name})

    def get_artifact(self, name, default=None):
        return self._state["artifacts"].get(name, default)

    # =====================================================
    # EVENTS
    # =====================================================

    def _log_event(self, event_type, payload=None):
        self._events.append({
            "type": event_type,
            "payload": payload or {}
        })

    def events(self):
        return list(self._events)

    # =====================================================
    # DEBUG
    # =====================================================

    def dump(self):
        return {
            "state": self._state,
            "events": self._events
        }