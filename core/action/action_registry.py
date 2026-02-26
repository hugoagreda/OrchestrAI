import importlib
import pkgutil
import core.action


def discover_actions():

    registry = {}

    # Iterar módulos dentro de core.action
    for _, module_name, _ in pkgutil.iter_modules(core.action.__path__):

        if module_name == "action_registry":
            continue

        module = importlib.import_module(f"core.action.{module_name}")

        module_namespace = getattr(module, "NAMESPACE", None)

        if not module_namespace and "_" in module_name:
            module_namespace = module_name.split("_", 1)[0]

        for attr in dir(module):
            fn = getattr(module, attr)

            if callable(fn) and not attr.startswith("_"):

                # 🔥 OS-native capability registry
                capability_key = f"{module_name}.{attr}"
                registry[capability_key] = fn

                # Namespace-native key (capability.action)
                if module_namespace:
                    namespace_key = f"{module_namespace}.{attr}"
                    registry[namespace_key] = fn

                # -------------------------------------------------
                # Legacy fallback (temporary)
                # -------------------------------------------------
                # Esto se eliminará cuando el sistema sea 100% capability-driven
                if attr not in registry:
                    registry[attr] = fn

    return registry