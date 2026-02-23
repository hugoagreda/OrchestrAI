from core.entity_engine.entity_runtime import EntityRuntime
from core.planner_layer.planner_layer import PlannerLayer
from core.workflow_engine.workflow_engine import WorkflowEngine
from core.execution_layer.execution_layer import ExecutionLayer


# Engines
runtime_engine = EntityRuntime()
planner = PlannerLayer()
workflow_engine = WorkflowEngine()
executor = ExecutionLayer()


# 1️⃣ Crear entidad runtime
runtime_entity = runtime_engine.create_runtime("human_ai_creator")

print("\n--- RUNTIME ENTITY ---")
print(runtime_entity)


# 2️⃣ Crear plan
action_plan = planner.generate_plan(runtime_entity)

print("\n--- ACTION PLAN ---")
print(action_plan)


# 3️⃣ Crear workflow
workflow = workflow_engine.build_workflow(action_plan)

print("\n--- WORKFLOW ---")
print(workflow)


# 4️⃣ Ejecutar workflow 🔥
executor.execute(workflow)

# python -m core.test_run