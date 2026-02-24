class RuntimeStep:
    """
    Internal structured representation of a workflow step.
    Does NOT replace workflow YAML.
    Only stabilizes runtime execution.
    """

    def __init__(self, data: dict):

        self.name = data.get("name")
        self.role = data.get("role")
        self.capability = data.get("capability")
        self.raw = data  # 👈 mantiene compatibilidad total

    # -------------------------------------------------
    # Helper keys (para resolver sin repetir lógica)
    # -------------------------------------------------
    def capability_key(self):
        return self.capability

    def namespaced_key(self):
        if self.role and self.name:
            return f"{self.role}.{self.name}"
        return None

    def legacy_key(self):
        return self.name

    def to_dict(self):
        return self.raw
    
    def capability_namespace(self):
        if self.role and self.name:
            return f"{self.role}.{self.name}"
        return self.name