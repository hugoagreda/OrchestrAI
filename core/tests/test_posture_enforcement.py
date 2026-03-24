import unittest
from core.execution_layer.execution_layer import ExecutionLayer
from core.execution_layer.execution_context import ExecutionContext
from core.execution_layer.runtime_step import RuntimeStep


# ---------------------------------------------------------
# Fake Kernel (no ejecuta nada real)
# ---------------------------------------------------------
class FakeKernel:
    def __init__(self):
        self.executed_steps = []

    def execute(self, step, context):
        self.executed_steps.append((step.capability, step.action))

    async def execute_async(self, step, context):
        self.executed_steps.append((step.capability, step.action))

    def cache_stats(self):
        return {"hits": 0, "misses": 0, "size": 0}


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------
class TestPostureEnforcement(unittest.TestCase):

    def setUp(self):
        self.kernel = FakeKernel()
        self.executor = ExecutionLayer(self.kernel)
        self.context = ExecutionContext()

    # ---------------------------------------------
    # 1️⃣ Capability restringida
    # ---------------------------------------------
    def test_capability_restricted(self):
        self.context.set_runtime("execution_posture", {
            "restricted_capabilities": ["media.*"],
            "allowed_actions": [],
        })

        workflow = {
            "steps": [
                {"capability": "media", "action": "generate_media"}
            ]
        }

        self.executor.execute(workflow, self.context)

        # No debe ejecutarse en el kernel
        self.assertEqual(len(self.kernel.executed_steps), 0)

        metrics = self.context.metrics()
        self.assertEqual(metrics["failed_steps"], 1)

    # ---------------------------------------------
    # 2️⃣ Acción no permitida
    # ---------------------------------------------
    def test_action_not_allowed(self):
        self.context.set_runtime("execution_posture", {
            "restricted_capabilities": [],
            "allowed_actions": ["generate_script"],
        })

        workflow = {
            "steps": [
                {"capability": "content", "action": "generate_media"}
            ]
        }

        self.executor.execute(workflow, self.context)

        self.assertEqual(len(self.kernel.executed_steps), 0)

        metrics = self.context.metrics()
        self.assertEqual(metrics["failed_steps"], 1)

    # ---------------------------------------------
    # 3️⃣ Sin postura → ejecuta normal
    # ---------------------------------------------
    def test_no_posture_executes(self):
        workflow = {
            "steps": [
                {"capability": "content", "action": "generate_script"}
            ]
        }

        self.executor.execute(workflow, self.context)

        self.assertEqual(len(self.kernel.executed_steps), 1)

        metrics = self.context.metrics()
        self.assertEqual(metrics["successful_steps"], 1)


if __name__ == "__main__":
    unittest.main()