# Summary: Implements task classifier logic for the OrchestrAI runtime.
class TaskClassifier:
    """
    Clasificador determinista y ligero.

    Mantiene la clasificación en etapa temprana barata y explicable.
    """

    TASK_KEYWORDS = {
        "summarization": ("summary", "summarize", "resumen", "tl;dr"),
        "question_answering": ("question", "pregunta", "answer", "faq"),
        "coding": ("code", "python", "bug", "refactor", "implement"),
        "analysis": ("analyze", "analysis", "metric", "insight", "comparar"),
        "classification": ("classify", "label", "category", "categoriza"),
        "extraction": ("extract", "extraction", "emails", "entities", "parse"),
        "translation": ("translate", "traduce", "idioma", "language"),
        "generation": ("generate", "write", "create", "draft", "script", "business plan"),
    }

    SUBTYPE_KEYWORDS = {
        "summarization": (
            "summary", "summarize", "tl;dr", "resumen",
        ),
        "analysis": (
            "analyze", "analysis", "metric", "insight", "compare", "benchmark",
        ),
        "rewrite": (
            "rewrite", "rephrase", "paraphrase", "improve wording",
        ),
        "translation": (
            "translate", "traduce", "localize",
        ),
        "extraction": (
            "extract", "parse", "entities", "email", "phone",
        ),
        "classification": (
            "classify", "label", "categorize", "tag",
        ),
        "planning": (
            "plan", "roadmap", "strategy", "timeline",
        ),
        "coding": (
            "code", "python", "bug", "refactor", "implement",
        ),
        "qa": (
            "question", "answer", "faq",
        ),
    }

    ACTION_HINTS = {
        "generate_script": "text_generation",
        "analyze_metrics": "analysis",
        "summarize": "summarization",
        "translate": "translation",
    }

    TASK_MARKERS = {
        "analysis": ("analyze", "analysis", "evaluate", "diagnose"),
        "summarization": ("summarize", "summary", "tl;dr", "resumen"),
        "generation": ("generate", "write", "create", "draft"),
    }

    SUBTYPE_VALUES = {
        "rewrite",
        "summarization",
        "extraction",
        "qa",
        "planning",
        "coding",
        "classification",
    }

    SIMPLE_DETERMINISTIC_SUBTYPES = {
        "summarization",
        "rewrite",
        "translation",
        "extraction",
        "classification",
    }

    def classify(self, step) -> dict:
        action = (getattr(step, "action", "") or "").strip().lower()
        payload = getattr(step, "payload", {}) or {}

        prompt_text = self._extract_text(payload)
        token_estimate = self._estimate_tokens(prompt_text)
        expected_tokens = self._token_bucket(token_estimate)

        task_marker = self._task_marker(prompt_text)
        subtype = self._detect_subtype(action, prompt_text)

        if action in self.ACTION_HINTS and task_marker is None:
            task_type = self.ACTION_HINTS[action]
            source = "action_hint"
            confidence = 0.9
        else:
            task_type, confidence = self._match_keywords(action, prompt_text)
            source = "keyword_heuristic"

            if task_marker == "analysis":
                task_type = "analysis"
            elif task_marker == "summarization":
                task_type = "summarization"
            elif task_marker == "generation" and task_type not in {"analysis", "coding"}:
                task_type = "generation"

        complexity = self._complexity(token_estimate)
        latency_sensitivity = self._latency_sensitivity(prompt_text, token_estimate)
        quality_requirement = self._quality_requirement(
            task_type=task_type,
            subtype=subtype,
            complexity=complexity,
            text=prompt_text,
            token_estimate=token_estimate,
        )
        deterministic = self._is_deterministic(task_type, subtype, prompt_text)

        # Keep expected_tokens/confidence/source for compatibility with current traces/tests.
        result = {
            "task_type": task_type,
            "subtype": subtype,
            "complexity": complexity,
            "quality_requirement": quality_requirement,
            "deterministic": deterministic,
            "token_estimate": token_estimate,
            "expected_tokens": expected_tokens,
            "latency_sensitivity": latency_sensitivity,
            "confidence": confidence,
            "source": source,
        }

        validated = self._validate_result(result)
        print(f"[TASK CLASSIFIER] {validated}")
        return validated

    def _extract_text(self, payload: dict) -> str:
        text_parts = []

        for key in ("prompt", "text", "input", "topic", "question"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                text_parts.append(value.strip())

        if not text_parts:
            text_parts.append(str(payload))

        return " ".join(text_parts)

    def _estimate_tokens(self, text: str) -> int:
        normalized = (text or "").strip()
        if not normalized:
            return 0

        return max(1, len(normalized) // 4)

    def _token_bucket(self, token_estimate: int) -> str:
        if token_estimate >= 400:
            return "large"
        if token_estimate >= 120:
            return "medium"
        return "small"

    def _complexity(self, token_estimate: int) -> str:
        if token_estimate < 50:
            return "low"
        if token_estimate < 500:
            return "medium"
        return "high"

    def _latency_sensitivity(self, text: str, token_estimate: int) -> str:
        normalized = (text or "").lower()
        high_markers = ("quick", "quickly", "fast", "asap", "urgent", "immediately")
        if any(marker in normalized for marker in high_markers):
            return "high"
        if token_estimate <= 80:
            return "medium"
        return "low"

    def _quality_requirement(
        self,
        task_type: str,
        subtype: str,
        complexity: str,
        text: str,
        token_estimate: int,
    ) -> str:
        normalized = (text or "").lower()

        # Default to medium for cost-aware routing.
        quality = "medium"

        low_quality_subtypes = {"extraction"}
        formatting_markers = ("format", "reformat", "formatting", "capitalize", "lowercase")

        if subtype in low_quality_subtypes:
            return "low"

        if subtype == "rewrite" and complexity in {"low", "medium"}:
            return "low"

        if any(marker in normalized for marker in formatting_markers):
            return "low"

        long_analysis = task_type == "analysis" and token_estimate >= 500
        complex_reasoning = any(
            marker in normalized
            for marker in ("reason", "causal", "trade-off", "hypothesis", "root cause", "infer")
        )
        multi_step_generation = task_type == "generation" and any(
            marker in normalized
            for marker in ("step by step", "multi-step", "first", "then", "outline", "sections")
        )

        if long_analysis or complex_reasoning or multi_step_generation:
            quality = "high"

        return quality

    def _is_deterministic(self, task_type: str, subtype: str, text: str) -> bool:
        if subtype in self.SIMPLE_DETERMINISTIC_SUBTYPES:
            return True

        normalized = (text or "").lower()
        deterministic_markers = (
            "convert", "format", "normalize", "extract", "summarize", "translate", "rephrase",
        )
        if any(marker in normalized for marker in deterministic_markers):
            return True

        return task_type in {"classification", "extraction", "translation", "summarization"}

    def _is_complex_generation(self, text: str) -> bool:
        normalized = (text or "").lower()
        complexity_markers = ("detailed", "including", "strategy", "business plan", "roadmap")
        return any(marker in normalized for marker in complexity_markers)

    def _detect_subtype(self, action: str, text: str) -> str:
        haystack = f"{action} {text}".lower()

        best_subtype = "classification"
        best_score = 0

        for subtype, keywords in self.SUBTYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in haystack)
            if score > best_score:
                best_subtype = subtype
                best_score = score

        if best_subtype not in self.SUBTYPE_VALUES:
            return "classification"

        return best_subtype

    def _validate_result(self, result: dict) -> dict:
        validated = result.copy()

        token_estimate = int(validated.get("token_estimate", 0) or 0)

        if token_estimate < 50 and validated.get("complexity") == "high":
            validated["complexity"] = "low"

        if validated.get("subtype") == "extraction" or validated.get("task_type") == "extraction":
            validated["deterministic"] = True

        if validated.get("subtype") not in self.SUBTYPE_VALUES:
            validated["subtype"] = "classification"

        if validated.get("quality_requirement") not in {"low", "medium", "high"}:
            validated["quality_requirement"] = "medium"

        return validated

    def _task_marker(self, text: str) -> str | None:
        normalized = (text or "").lower()
        for task_type, markers in self.TASK_MARKERS.items():
            if any(marker in normalized for marker in markers):
                return task_type
        return None

    def _match_keywords(self, action: str, text: str) -> tuple[str, float]:
        haystack = f"{action} {text}".lower()

        best_task = "generation"
        best_score = 0

        for task, keywords in self.TASK_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in haystack)
            if score > best_score:
                best_task = task
                best_score = score

        if best_score == 0:
            return "generation", 0.55

        confidence = min(0.95, 0.6 + (best_score * 0.1))
        return best_task, confidence
