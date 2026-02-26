import importlib
import inspect
import yaml
from pathlib import Path


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
    def __init__(self):
        self._handler_cache = {}
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
        }
        self.manifests = {}
        self.base_path = Path("core/action")
        self._boot_sequence()

    def cache_stats(self) -> dict:
        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "size": len(self._handler_cache),
        }

    def _validate_manifest(self, manifest_path: Path, config: dict) -> dict:
        if not isinstance(config, dict):
            raise ManifestValidationError(f"Invalid manifest format: {manifest_path}")

        namespace = config.get("namespace")
        if not isinstance(namespace, str) or not namespace.strip():
            raise ManifestValidationError(f"Manifest missing valid namespace: {manifest_path}")

        actions = config.get("actions")
        if not isinstance(actions, dict) or not actions:
            raise ManifestValidationError(f"Manifest missing actions map: {manifest_path}")

        for action_name, action_config in actions.items():
            if not isinstance(action_config, dict):
                raise ManifestValidationError(
                    f"Action '{action_name}' config must be a map in {manifest_path}"
                )

            handler = action_config.get("handler")
            if not isinstance(handler, str) or "." not in handler:
                raise ManifestValidationError(
                    f"Action '{action_name}' missing valid handler in {manifest_path}"
                )

            required_payload = action_config.get("required_payload", [])
            if not isinstance(required_payload, list):
                raise ManifestValidationError(
                    f"Action '{action_name}' required_payload must be a list in {manifest_path}"
                )

        return config

    def _boot_sequence(self):
        """Escaneo inicial de todas las capacidades instaladas."""
        print("\n[KERNEL BOOT] Loading capabilities...")
        boot_errors = []

        for manifest_path in self.base_path.glob("**/capability.yaml"):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    config = self._validate_manifest(manifest_path, config)
                    ns = config.get("namespace")
                    self.manifests[ns] = {
                        "config": config,
                        "path": manifest_path.parent
                    }
                    print(f"  -> [LOADED] {ns} (v{config.get('version')})")
            except Exception as e:
                boot_errors.append(f"{manifest_path}: {e}")
                print(f"  -> [FAILED] {manifest_path}: {e}")

        if boot_errors:
            details = "\n".join(boot_errors)
            raise ManifestValidationError(f"Kernel boot failed due to invalid manifests:\n{details}")

    def _validate_payload(self, step, manifest: dict):
        required = manifest["actions"][step.action].get("required_payload", [])
        missing = [field for field in required if field not in step.payload]

        if missing:
            missing_fields = ", ".join(missing)
            raise PayloadValidationError(
                f"Missing required payload for {step.capability}.{step.action}: {missing_fields}"
            )

    def _run_lifecycle_hook(self, handler, hook_name: str, step, context):
        module = importlib.import_module(handler.__module__)
        hook = getattr(module, hook_name, None)

        if callable(hook):
            try:
                hook(step, context)
            except Exception as e:
                raise CapabilityKernelError(
                    f"Lifecycle hook '{hook_name}' failed for {step.capability}.{step.action}: {e}"
                ) from e

    def _resolve_handler(self, step):
        """Busca el código ejecutable basado en el manifiesto."""
        cache_key = step.capability_key() or f"{step.capability}.{step.action}"
        if cache_key in self._handler_cache:
            self._cache_stats["hits"] += 1
            return self._handler_cache[cache_key]

        self._cache_stats["misses"] += 1

        ns_info = self.manifests.get(step.capability)
        if not ns_info:
            raise NamespaceNotInstalledError(
                f"Namespace '{step.capability}' not installed."
            )

        action_config = ns_info["config"]["actions"].get(step.action)
        if not action_config:
            raise ActionNotFoundError(
                f"Action '{step.action}' not found in namespace '{step.capability}'."
            )

        # Importación dinámica: core.action.content.content_actions
        handler_path = action_config["handler"] # "content_actions.generate_script"
        module_name, func_name = handler_path.split(".")
        
        full_module_path = f"core.action.{step.capability}.{module_name}"
        
        try:
            module = importlib.import_module(full_module_path)
            handler = getattr(module, func_name)
            self._handler_cache[cache_key] = handler
            return handler
        except Exception as e:
            raise HandlerResolutionError(
                f"Could not import handler '{handler_path}' from '{full_module_path}': {e}"
            ) from e

    def _execute_handler(self, handler, step, context):
        result = handler(step, context)
        if inspect.isawaitable(result):
            raise CapabilityKernelError(
                f"Async handler returned awaitable in sync path for {step.capability}.{step.action}. "
                "Use execute_async()."
            )

    async def _execute_handler_async(self, handler, step, context):
        result = handler(step, context)
        if inspect.isawaitable(result):
            await result

    def execute(self, step, context):
        """Ejecución con Pre-flight Check."""
        # 1. Resolver Handler y validar namespace/action
        handler = self._resolve_handler(step)

        # 2. Gobernanza: Validar Payload (Pre-flight)
        manifest = self.manifests[step.capability]["config"]
        self._validate_payload(step, manifest)
        
        # 3. Lifecycle pre-hook
        self._run_lifecycle_hook(handler, "on_start", step, context)

        # 4. Ejecución (Ring 0) + Lifecycle post-hook
        print(f"[KERNEL EXECUTE] {step.capability}.{step.action}")
        try:
            self._execute_handler(handler, step, context)
        except Exception as e:
            raise CapabilityKernelError(
                f"Execution failed for {step.capability}.{step.action}: {e}"
            ) from e
        finally:
            self._run_lifecycle_hook(handler, "on_finish", step, context)

    async def execute_async(self, step, context):
        """Async-ready execution path with same validations and lifecycle semantics."""
        handler = self._resolve_handler(step)
        manifest = self.manifests[step.capability]["config"]
        self._validate_payload(step, manifest)
        self._run_lifecycle_hook(handler, "on_start", step, context)

        print(f"[KERNEL EXECUTE] {step.capability}.{step.action}")
        try:
            await self._execute_handler_async(handler, step, context)
        except Exception as e:
            raise CapabilityKernelError(
                f"Execution failed for {step.capability}.{step.action}: {e}"
            ) from e
        finally:
            self._run_lifecycle_hook(handler, "on_finish", step, context)