from core.entity_engine.entity_runtime import EntityRuntime
from core.execution_layer.execution_context import ExecutionContext
from core.planner_layer.planner_layer import PlannerLayer
from core.workflow_engine.workflow_engine import WorkflowEngine
from core.execution_layer.execution_layer import ExecutionLayer
from core.behavior_engine.behavior_engine import BehaviorEngine
from core.strategy_engine.strategy_engine import StrategyEngine


# Engines
runtime_engine = EntityRuntime()
planner = PlannerLayer()
workflow_engine = WorkflowEngine()
executor = ExecutionLayer()
behavior_engine = BehaviorEngine()
strategy_engine = StrategyEngine()

# 1️⃣ Crear entidad runtime
runtime_entity = runtime_engine.create_runtime("human_ai_creator")

print("\n--- RUNTIME ENTITY ---")
print(runtime_entity)


# 2️⃣ Crear plan
action_plan = planner.generate_plan(runtime_entity)
action_plan = behavior_engine.adapt_intent(action_plan, runtime_entity)
action_plan = strategy_engine.apply_strategy(action_plan, runtime_entity)
print("\n--- ACTION PLAN ---")
print(action_plan.to_dict())


# 3️⃣ Crear workflow
workflow = workflow_engine.build_workflow(action_plan.to_dict())

print("\n--- WORKFLOW ---")
print(workflow)

# 4️⃣ Crear ExecutionContext (SSOT)
context = ExecutionContext()

# 🔥 Hydration inicial (esto es el paso 1 real)
context.load_identity(runtime_entity["identity"])
context.load_behavior(runtime_entity["behavior"])

# 5️⃣ Ejecutar workflow
executor.execute(workflow, context)

# python -m core.test_run