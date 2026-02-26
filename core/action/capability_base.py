class BaseCapability:

    namespace = None  # ej: "content"

    def __init__(self, registry: dict):
        self.registry = registry

    # -------------------------------------------------
    # Resolve action handler
    # -------------------------------------------------
    def resolve_action(self, action: str):

        # OS-native capability key
        namespace_key = f"{self.namespace}.{action}"
        handler = self.registry.get(namespace_key)

        if handler:
            return handler

        # Namespace → module mapping (OS layer)
        namespace_module_map = {
            "content": "content_generate_script",
            "publishing": "publishing_prepare_publish",
            "media": "media_action",
            "analytics": "analytics_action",
        }

        module = namespace_module_map.get(self.namespace)

        if not module:
            return None

        key = f"{module}.{action}"

        return self.registry.get(key)

    # -------------------------------------------------
    # Execute action
    # -------------------------------------------------
    def execute(self, action: str, context):

        handler = self.resolve_action(action)

        if not handler:
            print(f"[CAPABILITY] Unknown action: {self.namespace}.{action}")
            return
        
        # 🔥 lifecycle finish
        self.on_start(action, context)
    
        handler(context)

        # lifecycle finish
        self.on_finish(action, context)