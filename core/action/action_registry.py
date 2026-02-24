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

        for attr in dir(module):
            fn = getattr(module, attr)

            if callable(fn) and not attr.startswith("_"):

                # ✔️ registro clásico (backward compatible)
                registry[attr] = fn

                # 🔥 nuevo registro por namespace
                capability_key = f"{module_name}.{attr}"
                registry[capability_key] = fn

    return registry