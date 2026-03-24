# Summary: Implements intent step logic for the OrchestrAI runtime.
class IntentStep:

    def __init__(self, data: dict):

        # 🔥 RAW DATA (source of truth)
        self.raw = data or {}

        # 🔥 Promote core fields to root
        self._promote_fields()

    # =====================================================
    # FIELD PROMOTION (OS CONTRACT)
    # =====================================================

    def _promote_fields(self):

        for key, value in self.raw.items():
            setattr(self, key, value)

    # =====================================================
    # UPDATE RAW (used by StrategyEngine)
    # =====================================================

    def update(self, data: dict):

        if not data:
            return

        self.raw.update(data)
        self._promote_fields()

    # =====================================================
    # SERIALIZATION
    # =====================================================

    def to_dict(self):
        return self.raw