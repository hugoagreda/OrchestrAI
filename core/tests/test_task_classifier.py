# python -m core.tests.test_task_classifier

import unittest
import sys
from pathlib import Path

# Permite ejecutar este archivo directamente desde la raiz del repo.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
        self.assertIn("subtype", result)
        self.assertIn("quality_requirement", result)
        self.assertIn("deterministic", result)
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

    def test_summarization_task_quality(self):
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {"prompt": "Summarize this article about climate change"},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["task_type"], "summarization")
        self.assertEqual(result["subtype"], "summarization")
        self.assertIn(result["complexity"], {"low", "medium"})

    def test_extraction_task_quality(self):
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {"prompt": "Extract all emails from this text"},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["task_type"], "extraction")
        self.assertEqual(result["deterministic"], True)

    def test_generation_task_complexity_high(self):
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {
                "prompt": "Write a detailed business plan for a SaaS startup including GTM strategy. " * 150,
            },
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["task_type"], "generation")
        self.assertEqual(result["complexity"], "high")

    def test_short_prompt_sets_low_complexity(self):
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {"prompt": "Summarize this note."},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["complexity"], "low")

    def test_long_prompt_sets_high_complexity(self):
        long_prompt = "Analyze this report thoroughly and provide recommendations. " * 800
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {"prompt": long_prompt},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["complexity"], "high")

    def test_analytical_tasks_require_high_quality(self):
        step = RuntimeStep({
            "capability": "analytics",
            "action": "assist",
            "payload": {"prompt": "Analyze campaign KPIs and explain root causes."},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["task_type"], "analysis")
        self.assertEqual(result["quality_requirement"], "high")

    def test_simple_transformation_is_deterministic(self):
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {"prompt": "Rephrase this sentence in plain Spanish."},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["deterministic"], True)

    def test_rewrite_quality_requirement_low_or_medium(self):
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {"prompt": "Rephrase this sentence with simpler words."},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["subtype"], "rewrite")
        self.assertIn(result["quality_requirement"], {"low", "medium"})

    def test_subtype_never_returns_general(self):
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {"prompt": "Hello"},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertNotEqual(result["subtype"], "general")

    def test_expected_tokens_large_for_long_input(self):
        long_text = "climate policy and market signals " * 1500
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {"prompt": long_text},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["expected_tokens"], "large")

    def test_latency_sensitivity_high(self):
        step = RuntimeStep({
            "capability": "content",
            "action": "assist",
            "payload": {"prompt": "Quickly rephrase this sentence"},
            "metadata": {},
        })

        result = self.classifier.classify(step)
        self.assertEqual(result["latency_sensitivity"], "high")


if __name__ == "__main__":
    unittest.main()
