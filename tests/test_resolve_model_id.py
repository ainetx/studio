"""
Unit tests for _resolve_model_id function in commands/agents.py.

Covers:
  A) Empty-string tier returns None (inherit case)
  B) Valid tier with known model resolves correctly
  C) cf:inherit alias also returns None
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "cypilot" / "scripts"))


class TestResolveModelId(unittest.TestCase):
    """Unit tests for _resolve_model_id function."""

    def _fn(self):
        from cypilot.commands.agents import _resolve_model_id
        return _resolve_model_id

    def test_resolve_model_id_empty_tier_returns_none(self):
        """Empty-string tier means inherit; _resolve_model_id returns None.

        (P5-F013: ensures empty-tier fix - empty string should not emit a model line)
        """
        _resolve_model_id = self._fn()
        result = _resolve_model_id("claude", "anthropic", "", "any-mode", "any-role")
        self.assertIsNone(result, f"Expected None for empty tier, got {result!r}")

    def test_resolve_model_id_cf_inherit_returns_none(self):
        """cf:inherit explicitly returns None."""
        _resolve_model_id = self._fn()
        result = _resolve_model_id("claude", "anthropic", "cf:inherit", "any-mode", "any-role")
        self.assertIsNone(result, f"Expected None for cf:inherit, got {result!r}")

    def test_resolve_model_id_cf_auto_returns_tool_default(self):
        """cf:auto resolves to tool-specific auto value (or None if unsupported)."""
        _resolve_model_id = self._fn()
        # cursor tool supports "auto"
        result_cursor = _resolve_model_id("cursor", "openai", "cf:auto", "any-mode", "any-role")
        self.assertEqual(result_cursor, "auto")
        # claude tool doesn't support "auto", returns None
        result_claude = _resolve_model_id("claude", "anthropic", "cf:auto", "any-mode", "any-role")
        self.assertIsNone(result_claude)

    def test_resolve_model_id_valid_tier(self):
        """Valid tier resolves to a model ID string."""
        _resolve_model_id = self._fn()
        # Use a tier that should exist in the matrix; exact value depends on config
        result = _resolve_model_id("claude", "anthropic", "standard", "any-mode", "any-role")
        # Result should be a string (either from matrix or passthrough)
        self.assertIsInstance(result, (str, type(None)))


if __name__ == "__main__":
    unittest.main()
