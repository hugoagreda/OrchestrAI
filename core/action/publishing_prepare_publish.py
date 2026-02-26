from core.action.capability_base import BaseCapability

CAPABILITY = "publishing.prepare_publish"
NAMESPACE = "publishing"


class Capability(BaseCapability):

    namespace = NAMESPACE

    def on_start(self, action, context):
        print(f"[PUBLISHING CAPABILITY] starting {action}")

    def on_finish(self, action, context):
        print(f"[PUBLISHING CAPABILITY] finished {action}")


def prepare_publish(context):
    print("🚀 Preparing publish (mock)...")

    media = context.get("media_assets")
    if media:
        context.set("publish_ready", True)