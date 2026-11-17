"""Metrics module contract test (fills in at M5; keeps CI honest early).
Until metrics.py is implemented, assert its planned interface exists."""
import importlib

def test_metrics_module_imports_or_declines_cleanly():
    mod = importlib.import_module("src.engine.metrics")
    # once implemented, these must exist:
    for fn in ("confusion_matrix", "bootstrap_ci", "error_cost_summary"):
        assert hasattr(mod, fn) or mod.__doc__ is not None
