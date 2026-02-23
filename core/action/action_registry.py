# OrchestrAI - Action Registry
# Auto-discovers action handlers inside core/action/

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
                registry[attr] = fn

    return registry