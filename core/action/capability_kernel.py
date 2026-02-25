from core.action.content_capability import ContentCapability
from core.action.capability_base import BaseCapability

class PublishingCapability(BaseCapability):

    namespace = "publishing"

    def on_start(self, action, context):
        print(f"[PUBLISHING CAPABILITY] starting {action}")

    def on_finish(self, action, context):
        print(f"[PUBLISHING CAPABILITY] finished {action}")

class CapabilityKernel:

    def __init__(self, registry: dict):

        self.registry = registry

        # 🔥 Capability registry OS-level
        self.capabilities = {
            "content": ContentCapability(registry),
            "publishing": PublishingCapability(registry),
        }

    # -------------------------------------------------
    # Resolve capability object
    # -------------------------------------------------
    def resolve_capability(self, namespace: str):

        return self.capabilities.get(namespace)

    # -------------------------------------------------
    # Execute through kernel boundary
    # -------------------------------------------------
    def execute(self, step, context):

        capability = self.resolve_capability(step.capability)

        if not capability:
            print(f"[KERNEL] Unknown capability namespace: {step.capability}")
            return

        capability.execute(step.action, context)