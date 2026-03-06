import unittest

from core.action.task_classifier import TaskClassifier
from core.execution_layer.runtime_step import RuntimeStep


class TaskClassifierTests(unittest.TestCase):
    def setUp(self):
        self.classifier = TaskClassifier()

    def test_action_hint_classification(self):
        step = RuntimeStep({
            "capability": "content",
            "action": "generate_script",
            "payload": {"topic": "AI infra"},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["task_type"], "text_generation")
        self.assertEqual(result["source"], "action_hint")

    def test_keyword_classification_coding(self):
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {"prompt": "Please refactor this Python code and fix bug"},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["task_type"], "coding")
        self.assertGreater(result["token_estimate"], 0)


if __name__ == "__main__":
    unittest.main()
