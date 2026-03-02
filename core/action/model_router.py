class ModelRouter:
    """
    Policy-aware model resolver (minimal deterministic version).
    """

    DEFAULT_DECISION = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "reason": "default_policy",
    }

    def resolve(self, namespace: str, action: str, posture: dict | None = None) -> dict:
        posture = posture or {}
        policy = posture.get("model_policy", {})

        # 1️⃣ Exact match: "namespace.action"
        exact_key = f"{namespace}.{action}"
        if exact_key in policy:
            decision = policy[exact_key].copy()
            decision.setdefault("reason", "strategy_exact_match")
            return decision

        # 2️⃣ Wildcard match: "namespace.*"
        wildcard_key = f"{namespace}.*"
        if wildcard_key in policy:
            decision = policy[wildcard_key].copy()
            decision.setdefault("reason", "strategy_wildcard_match")
            return decision

        # 3️⃣ Default
        return self.DEFAULT_DECISION.copy()