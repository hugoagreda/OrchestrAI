class RuntimeStep:
    """
    OS-native runtime step.

    Execution ABI:
        capability.namespace + action

    Agents are NOT part of execution anymore.
    """

    def __init__(self, data: dict):

        self.action = data.get("action")
        self.capability = data.get("capability")

        # metadata opcional
        self.metadata = data.get("metadata", {})
        self.raw = data

    # -------------------------------------------------
    # OS-native key
    # -------------------------------------------------
    def capability_action_key(self):
        if self.capability and self.action:
            return f"{self.capability}.{self.action}"
        return None

    # -------------------------------------------------
    # Legacy fallback (temporary)
    # -------------------------------------------------
    def action_key(self):
        return self.action

    def to_dict(self):
        return self.raw