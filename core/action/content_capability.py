from core.action.capability_base import BaseCapability


class ContentCapability(BaseCapability):

    namespace = "content"

    def on_start(self, action, context):
        print(f"[CONTENT CAPABILITY] starting {action}")

    def on_finish(self, action, context):
        print(f"[CONTENT CAPABILITY] finished {action}")