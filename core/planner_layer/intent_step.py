class IntentStep:
    """
    High-level planner output.
    Represents intention, NOT execution.
    """

    def __init__(self, data: dict):
        self.objective = data.get("objective")
        self.content_type = data.get("content_type")
        self.platform = data.get("platform")
        self.tone = data.get("tone")
        self.visual_style = data.get("visual_style")
        self.raw = data

    def to_dict(self):
        return self.raw