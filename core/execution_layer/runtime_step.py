# Summary: Implements runtime step logic for the OrchestrAI runtime.
class RuntimeStep:

    def __init__(self, data_or_capability, action=None, payload=None, metadata=None, strategy=None):

        if isinstance(data_or_capability, dict):
            data = data_or_capability
        else:
            data = {
                "capability": data_or_capability,
                "action": action,
                "payload": payload or {},
                "metadata": metadata or {},
                "strategy": strategy or {},
            }

        # -------------------------------------------------
        # OS-Native Fields
        # -------------------------------------------------
        self.capability = data.get("capability")
        self.action = data.get("action")

        # Opcionales
        self.payload = data.get("payload", {})
        self.metadata = data.get("metadata", {})
        self.strategy = data.get("strategy", {})

        # Raw debug snapshot
        self.raw = data

    # -------------------------------------------------
    # Capability Resolution Keys
    # -------------------------------------------------
    def capability_key(self):
        """
        OS-native key:
        capability.action
        """
        if self.capability and self.action:
            return f"{self.capability}.{self.action}"
        return None

    def legacy_key(self):
        """
        Backward compatibility fallback.
        """
        return self.action

    # -------------------------------------------------
    # Debug helper
    # -------------------------------------------------
    def to_dict(self):
        return self.raw