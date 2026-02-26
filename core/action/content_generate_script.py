from core.action.capability_base import BaseCapability

# 🔥 OS-native capability definition
CAPABILITY = "content.generate_script"
NAMESPACE = "content"


class Capability(BaseCapability):

    namespace = NAMESPACE

    def on_start(self, action, context):
        print(f"[CONTENT CAPABILITY] starting {action}")

    def on_finish(self, action, context):
        print(f"[CONTENT CAPABILITY] finished {action}")


# 🔥 Executable action (auto-discovered by registry)
def generate_script(context):
    print("🧠 Generating script (mock)...")
    context.set("script", "This is a mock generated script")