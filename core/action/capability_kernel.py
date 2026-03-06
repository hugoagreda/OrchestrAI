import importlib
import inspect
import yaml
from pathlib import Path
from .model_router import ModelRouter
from .task_classifier import TaskClassifier
from .model_adapters import ModelAdapterRegistry


class CapabilityKernelError(Exception):
    pass


class ManifestValidationError(CapabilityKernelError):
    pass


class NamespaceNotInstalledError(CapabilityKernelError):
    pass


class ActionNotFoundError(CapabilityKernelError):
    pass


class HandlerResolutionError(CapabilityKernelError):
    pass


class PayloadValidationError(CapabilityKernelError):
    pass


class CapabilityKernel:
    """
    Núcleo de Ejecución Gobernado por Capacidades.

    Responsabilidades:
    - Validación de manifiestos (en arranque)
    - Resolución de namespaces
    - Despacho de acciones
    - Validación de payload (pre-ejecución)
    - Orquestación de hooks de ciclo de vida
    - Caché de handlers
    - Ejecución síncrona y asíncrona
    - Enrutamiento de modelos por política (posture-aware)
    """

    def __init__(self):
        self._handler_cache = {}
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
        }
        self.manifests = {}
        self.base_path = Path("core/action")
        self._boot_sequence()
        self.model_router = ModelRouter()
        self.task_classifier = TaskClassifier()
        self.adapter_registry = ModelAdapterRegistry()

    # ------------------------------------------------------------------
    # Telemetría de caché
    # ------------------------------------------------------------------

    def cache_stats(self) -> dict:
        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "size": len(self._handler_cache),
        }

    # ------------------------------------------------------------------
    # Arranque y validación de manifiestos
    # ------------------------------------------------------------------

    def _validate_manifest(self, manifest_path: Path, config: dict) -> dict:
        if not isinstance(config, dict):
            raise ManifestValidationError(f"Formato de manifiesto inválido: {manifest_path}")

        namespace = config.get("namespace")
        if not isinstance(namespace, str) or not namespace.strip():
            raise ManifestValidationError(
                f"El manifiesto no define un namespace válido: {manifest_path}"
            )

        actions = config.get("actions")
        if not isinstance(actions, dict) or not actions:
            raise ManifestValidationError(
                f"El manifiesto no define mapa de acciones: {manifest_path}"
            )

        for action_name, action_config in actions.items():
            if not isinstance(action_config, dict):
                raise ManifestValidationError(
                    f"La configuración de la acción '{action_name}' debe ser un mapa en {manifest_path}"
                )

            handler = action_config.get("handler")
            if not isinstance(handler, str) or "." not in handler:
                raise ManifestValidationError(
                    f"La acción '{action_name}' no define un handler válido en {manifest_path}"
                )

            required_payload = action_config.get("required_payload", [])
            if not isinstance(required_payload, list):
                raise ManifestValidationError(
                    f"La acción '{action_name}' debe definir required_payload como lista en {manifest_path}"
                )

        return config

    def _boot_sequence(self):
        print("\n[KERNEL BOOT] Cargando capacidades...")
        boot_errors = []

        for manifest_path in self.base_path.glob("**/capability.yaml"):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    config = self._validate_manifest(manifest_path, config)

                    namespace = config["namespace"]
                    self.manifests[namespace] = {
                        "config": config,
                        "path": manifest_path.parent,
                    }

                    print(f"  -> [LOADED] {namespace} (v{config.get('version')})")

            except Exception as e:
                boot_errors.append(f"{manifest_path}: {e}")
                print(f"  -> [FAILED] {manifest_path}: {e}")

        if boot_errors:
            details = "\n".join(boot_errors)
            raise ManifestValidationError(
                f"El arranque del kernel falló por manifiestos inválidos:\n{details}"
            )

    # ------------------------------------------------------------------
    # Validación y resolución de handlers
    # ------------------------------------------------------------------

    def _validate_payload(self, step, manifest: dict):
        required = manifest["actions"][step.action].get("required_payload", [])
        missing = [field for field in required if field not in step.payload]

        if missing:
            raise PayloadValidationError(
                f"Falta payload requerido para "
                f"{step.capability}.{step.action}: {', '.join(missing)}"
            )

    def _resolve_handler(self, step):
        cache_key = step.capability_key() or f"{step.capability}.{step.action}"

        if cache_key in self._handler_cache:
            self._cache_stats["hits"] += 1
            return self._handler_cache[cache_key]

        self._cache_stats["misses"] += 1

        ns_info = self.manifests.get(step.capability)
        if not ns_info:
            raise NamespaceNotInstalledError(
                f"El namespace '{step.capability}' no está instalado."
            )

        action_config = ns_info["config"]["actions"].get(step.action)
        if not action_config:
            raise ActionNotFoundError(
                f"La acción '{step.action}' no existe en el namespace '{step.capability}'."
            )

        handler_path = action_config["handler"]
        module_name, func_name = handler_path.split(".")
        full_module_path = f"core.action.{step.capability}.{module_name}"

        try:
            module = importlib.import_module(full_module_path)
            handler = getattr(module, func_name)
            self._handler_cache[cache_key] = handler
            return handler

        except Exception as e:
            raise HandlerResolutionError(
                f"No se pudo importar el handler '{handler_path}' "
                f"desde '{full_module_path}': {e}"
            ) from e

    # ------------------------------------------------------------------
    # Ejecución síncrona
    # ------------------------------------------------------------------

    def execute(self, step, context):
        handler = self._resolve_handler(step)

        manifest = self.manifests[step.capability]["config"]
        self._validate_payload(step, manifest)

        posture = context.get_posture() or {}
        classification = self.task_classifier.classify(step)
        routing_policy = posture.get("routing_policy", "balanced")

        model_decision = self.model_router.resolve(
            namespace=step.capability,
            action=step.action,
            posture=posture,
            context=context,
            task_type=classification.get("task_type"),
            token_size=classification.get("token_estimate"),
            routing_policy=routing_policy,
        )

        adapter = self.adapter_registry.get(model_decision.get("provider"))
        adapter_request = adapter.prepare_request(step, model_decision)

        context.log_model_decision(model_decision)
        context.log_execution_trace({
            "capability": step.capability,
            "action": step.action,
            "task_type": classification.get("task_type"),
            "classification_confidence": classification.get("confidence"),
            "token_size": classification.get("token_estimate"),
            "routing_policy": routing_policy,
            "selected_provider": model_decision.get("provider"),
            "selected_model": model_decision.get("model"),
            "routing_reason": model_decision.get("reason"),
            "estimated_cost": model_decision.get("estimated_cost"),
            "estimated_latency": model_decision.get("estimated_latency"),
            "budget_remaining": model_decision.get("budget_remaining"),
            "budget_ratio": model_decision.get("budget_ratio"),
            "adapter": adapter.__class__.__name__,
            "adapter_provider": adapter_request.get("provider"),
        })

        self._run_lifecycle_hook(handler, "on_start", step, context)

        print(f"[KERNEL EXECUTE] {step.capability}.{step.action}")

        try:
            self._execute_handler(handler, step, context)
        except Exception as e:
            raise CapabilityKernelError(
                f"La ejecución falló para {step.capability}.{step.action}: {e}"
            ) from e
        finally:
            self._run_lifecycle_hook(handler, "on_finish", step, context)

    # ------------------------------------------------------------------
    # Ejecución asíncrona
    # ------------------------------------------------------------------

    async def execute_async(self, step, context):
        handler = self._resolve_handler(step)

        manifest = self.manifests[step.capability]["config"]
        self._validate_payload(step, manifest)

        posture = context.get_posture() or {}
        classification = self.task_classifier.classify(step)
        routing_policy = posture.get("routing_policy", "balanced")

        model_decision = self.model_router.resolve(
            namespace=step.capability,
            action=step.action,
            posture=posture,
            context=context,
            task_type=classification.get("task_type"),
            token_size=classification.get("token_estimate"),
            routing_policy=routing_policy,
        )

        adapter = self.adapter_registry.get(model_decision.get("provider"))
        adapter_request = adapter.prepare_request(step, model_decision)

        context.log_model_decision(model_decision)
        context.log_execution_trace({
            "capability": step.capability,
            "action": step.action,
            "task_type": classification.get("task_type"),
            "classification_confidence": classification.get("confidence"),
            "token_size": classification.get("token_estimate"),
            "routing_policy": routing_policy,
            "selected_provider": model_decision.get("provider"),
            "selected_model": model_decision.get("model"),
            "routing_reason": model_decision.get("reason"),
            "estimated_cost": model_decision.get("estimated_cost"),
            "estimated_latency": model_decision.get("estimated_latency"),
            "budget_remaining": model_decision.get("budget_remaining"),
            "budget_ratio": model_decision.get("budget_ratio"),
            "adapter": adapter.__class__.__name__,
            "adapter_provider": adapter_request.get("provider"),
        })

        self._run_lifecycle_hook(handler, "on_start", step, context)

        print(f"[KERNEL EXECUTE] {step.capability}.{step.action}")

        try:
            await self._execute_handler_async(handler, step, context)
        except Exception as e:
            raise CapabilityKernelError(
                f"La ejecución falló para {step.capability}.{step.action}: {e}"
            ) from e
        finally:
            self._run_lifecycle_hook(handler, "on_finish", step, context)

    # ------------------------------------------------------------------
    # Invocación de handlers
    # ------------------------------------------------------------------

    def _execute_handler(self, handler, step, context):
        result = handler(step, context)

        if inspect.isawaitable(result):
            raise CapabilityKernelError(
                f"Un handler async devolvió un awaitable en la ruta síncrona para "
                f"{step.capability}.{step.action}. Usa execute_async()."
            )

    async def _execute_handler_async(self, handler, step, context):
        result = handler(step, context)

        if inspect.isawaitable(result):
            await result

    # ------------------------------------------------------------------
    # Hooks de ciclo de vida
    # ------------------------------------------------------------------

    def _run_lifecycle_hook(self, handler, hook_name: str, step, context):
        module = importlib.import_module(handler.__module__)
        hook = getattr(module, hook_name, None)

        if callable(hook):
            try:
                hook(step, context)
            except Exception as e:
                raise CapabilityKernelError(
                    f"El hook de ciclo de vida '{hook_name}' falló para "
                    f"{step.capability}.{step.action}: {e}"
                ) from e