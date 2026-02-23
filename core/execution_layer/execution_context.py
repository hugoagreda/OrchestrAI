# OrchestrAI - Execution Context v1.5
# Structured runtime state + lightweight event log.


class ExecutionContext:
    """
    Shared runtime state container.
    Acts as:
        - State store
        - Artifact registry
        - Event log (future orchestration ready)
    """

    def __init__(self):

        # -------------------------
        # CORE STATE (structured)
        # -------------------------
        self._state = {
            "identity": {},
            "behavior": {},
            "execution": {
                "script": None,
                "media_assets": [],
                "publish_ready": False
            },
            "artifacts": {}
        }

        # -------------------------
        # EVENT LOG (very important)
        # -------------------------
        self._events = []

    # =====================================================
    # STATE ACCESS
    # =====================================================

    def set(self, key, value):
        """
        Backward compatible setter.
        Writes into execution namespace by default.
        """
        self._state["execution"][key] = value
        self._log_event("STATE_UPDATED", {key: value})

    def get(self, key, default=None):
        return self._state["execution"].get(key, default)

    # =====================================================
    # ARTIFACTS (future-safe)
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