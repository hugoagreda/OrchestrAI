# Summary: Implements model adapters logic for the OrchestrAI runtime.
class BaseModelAdapter:
    provider = "base"

    def supports(self, provider: str) -> bool:
        return self.provider == (provider or "").lower()

    def prepare_request(self, step, model_decision: dict) -> dict:
        return {
            "provider": model_decision.get("provider"),
            "model": model_decision.get("model"),
            "capability": getattr(step, "capability", None),
            "action": getattr(step, "action", None),
            "payload": getattr(step, "payload", {}) or {},
            "metadata": getattr(step, "metadata", {}) or {},
        }


class OpenAIAdapter(BaseModelAdapter):
    provider = "openai"


class AnthropicAdapter(BaseModelAdapter):
    provider = "anthropic"


class GoogleAdapter(BaseModelAdapter):
    provider = "google"


class MistralAdapter(BaseModelAdapter):
    provider = "mistral"


class OpenRouterAdapter(BaseModelAdapter):
    provider = "openrouter"


class LocalModelAdapter(BaseModelAdapter):
    provider = "local"


class EnterpriseModelAdapter(BaseModelAdapter):
    provider = "enterprise"


class ModelAdapterRegistry:
    def __init__(self):
        self._adapters = [
            OpenAIAdapter(),
            AnthropicAdapter(),
            GoogleAdapter(),
            MistralAdapter(),
            OpenRouterAdapter(),
            LocalModelAdapter(),
            EnterpriseModelAdapter(),
        ]

    def get(self, provider: str) -> BaseModelAdapter:
        normalized = (provider or "").lower()

        for adapter in self._adapters:
            if adapter.supports(normalized):
                return adapter

        return BaseModelAdapter()
