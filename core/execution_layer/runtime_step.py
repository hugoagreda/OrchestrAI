class RuntimeStep:

    def __init__(self, data: dict):

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