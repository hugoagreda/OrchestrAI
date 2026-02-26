from core.entity_engine.entity_builder import EntityBuilder
from core.execution_layer.execution_context import ExecutionContext
from core.planner_layer.planner_layer import PlannerLayer
from core.strategy_engine.strategy_engine import StrategyEngine
from core.workflow_engine.workflow_engine import WorkflowEngine
from core.execution_layer.execution_layer import ExecutionLayer

# --- NUEVAS IMPORTACIONES PARA EL RING 0 ---
from core.action.capability_kernel import CapabilityKernel

# =====================================================
# 🧠 DEBUG HELPERS
# =====================================================

def debug_section(title):
    print("\n" + "=" * 50)
    print(f"[ {title} ]")
    print("=" * 50)


def debug_dump(label, data):
    print(f"\n--- {label} ---")

    # IntentStep introspection automática
    if hasattr(data, "__dict__"):
        try:
            print(data.__dict__)
            return
        except:
            pass

    print(data)


# =====================================================
# 🔥 DEFINITIVE TEST RUN (CONSOLIDATED)
# =====================================================

def main():

    # =====================================================
    # 0️⃣ KERNEL INITIALIZATION (OS BOOT)
    # =====================================================
    # Initialize kernel (manifest discovery via _boot_sequence)
    kernel = CapabilityKernel()

    # =====================================================
    # 1️⃣ ENTITY BUILD
    # =====================================================
    debug_section("ENTITY BUILD")

    builder = EntityBuilder()
    entity = builder.build_entity("human_ai_creator")

    debug_dump("RUNTIME ENTITY", entity)

    # =====================================================
    # 2️⃣ CONTEXT INIT
    # =====================================================
    debug_section("CONTEXT INIT")

    context = ExecutionContext()
    context.load_identity(entity.get("identity"))
    context.load_behavior(entity.get("behavior"))

    print("[CONTEXT] Identity + Behavior hydrated")

    # =====================================================
    # 3️⃣ PLANNER
    # =====================================================
    debug_section("PLANNER LAYER")

    planner = PlannerLayer()
    intent = planner.generate_plan(entity)

    debug_dump("ACTION PLAN (RAW)", intent)

    # =====================================================
    # 4️⃣ STRATEGY ENGINE
    # =====================================================
    debug_section("STRATEGY ENGINE")

    strategy = StrategyEngine()
    strategized_intent = strategy.apply_strategy(intent, entity)

    posture = {
        "restricted_capabilities": strategized_intent.to_dict().get("restricted_capabilities", []),
        "allowed_actions": strategized_intent.to_dict().get("allowed_actions", []),
        "autonomy": strategized_intent.to_dict().get("autonomy"),
    }

    context.set_runtime("execution_posture", posture)
    
    print("\n[POSTURE SNAPSHOT INJECTED]")
    print(posture)

    debug_dump("ACTION PLAN (STRATEGIZED - ROOT)", strategized_intent)

    if hasattr(strategized_intent, "raw"):
        debug_dump("ACTION PLAN (STRATEGIZED - RAW)", strategized_intent.raw)

        print("\n[INTENT CONTRACT CHECK]")

        root_keys = set(strategized_intent.__dict__.keys())
        raw_keys = set(strategized_intent.raw.keys())

        print("ROOT KEYS:", root_keys)
        print("RAW KEYS:", raw_keys)

        missing = raw_keys - root_keys

        if missing:
            print(f"[⚠️ STRATEGY NOT PROMOTED TO ROOT]: {missing}")
        else:
            print("[✅ STRATEGY PROMOTED CORRECTLY]")

    # =====================================================
    # 5️⃣ WORKFLOW ENGINE
    # =====================================================
    debug_section("WORKFLOW ENGINE")

    workflow_engine = WorkflowEngine()
    # Pasamos el diccionario que incluye el 'capability_map' inyectado por Strategy
    workflow = workflow_engine.build_workflow(strategized_intent.to_dict())

    debug_dump("WORKFLOW BUILT", workflow)

    if "steps" in workflow:
        print("\n[WORKFLOW STEPS]")
        for i, step in enumerate(workflow["steps"], 1):
            print(f"{i}. capability={step.get('capability')} | action={step.get('action')}")

    # =====================================================
    # 6️⃣ EXECUTION LAYER (INJECTED KERNEL)
    # =====================================================
    debug_section("EXECUTION LAYER")

    # Inyectamos el Kernel para cumplir con la nueva arquitectura
    executor = ExecutionLayer(kernel)

    print("\n[EXECUTION] Starting kernel dispatch...")
    executor.execute(workflow, context, enable_profiling=True)

    # =====================================================
    # 7️⃣ FINAL CONTEXT
    # =====================================================
    debug_section("FINAL CONTEXT SNAPSHOT")

    debug_dump("CONTEXT DUMP", context.dump())


# =====================================================
# ENTRYPOINT
# =====================================================
if __name__ == "__main__":
    main()

# Ejecución: python -m core.test_run