from core.action.capability_base import BaseCapability

class PublishingCapability(BaseCapability):

    namespace = "publishing"

    def on_start(self, action, context):
        print(f"[PUBLISHING CAPABILITY] starting {action}")

    def on_finish(self, action, context):
        print(f"[PUBLISHING CAPABILITY] finished {action}")