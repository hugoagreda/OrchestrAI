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
        "translation": ("translate", "traduce", "idioma", "language"),
        "text_generation": ("generate", "write", "create", "draft", "script"),
    }

    ACTION_HINTS = {
        "generate_script": "text_generation",
        "analyze_metrics": "analysis",
        "summarize": "summarization",
        "translate": "translation",
    }

    def classify(self, step) -> dict:
        action = (getattr(step, "action", "") or "").strip().lower()
        payload = getattr(step, "payload", {}) or {}

        prompt_text = self._extract_text(payload)
        token_estimate = self._estimate_tokens(prompt_text)

        if action in self.ACTION_HINTS:
            task_type = self.ACTION_HINTS[action]
            source = "action_hint"
            confidence = 0.9
        else:
            task_type, confidence = self._match_keywords(action, prompt_text)
            source = "keyword_heuristic"

        complexity = "high" if task_type in {"coding", "analysis", "question_answering"} else "low"
        if token_estimate > 1800:
            complexity = "high"

        return {
            "task_type": task_type,
            "complexity": complexity,
            "token_estimate": token_estimate,
            "confidence": confidence,
            "source": source,
        }

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

    def _match_keywords(self, action: str, text: str) -> tuple[str, float]:
        haystack = f"{action} {text}".lower()

        best_task = "text_generation"
        best_score = 0

        for task, keywords in self.TASK_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in haystack)
            if score > best_score:
                best_task = task
                best_score = score

        if best_score == 0:
            return "text_generation", 0.55

        confidence = min(0.95, 0.6 + (best_score * 0.1))
        return best_task, confidence
