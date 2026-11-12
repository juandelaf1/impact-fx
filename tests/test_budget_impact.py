import json
import unittest
from pathlib import Path

from backend.src.services.budget_impact import calculate_budget_impact


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUDGETS_PATH = PROJECT_ROOT / "data" / "processed" / "project_budgets.json"


class TestBudgetImpact(unittest.TestCase):
    def setUp(self):
        with BUDGETS_PATH.open(encoding="utf-8") as f:
            budgets = json.load(f)
        self.project = next(b for b in budgets if b["project_id"] == "KE-HEALTH-001")

    def test_b1_budget_coverage(self):
        result = calculate_budget_impact(1444200, 1400874, self.project)
        self.assertEqual(result["budget_total"], 1444200.0)
        self.assertEqual(result["base_coverage_pct"], 100.0)
        self.assertEqual(result["stress_coverage_pct"], 97.0)
        self.assertEqual(result["budget_gap"], 43326.0)
        self.assertEqual(result["budget_status"], "partial")
        self.assertTrue(result["is_synthetic_demo"])

    def test_invalid_or_empty_budget(self):
        result = calculate_budget_impact(1000, 900, {"items": []})
        self.assertEqual(result["budget_total"], 0.0)
        self.assertEqual(result["base_coverage_pct"], 0.0)
        self.assertEqual(result["stress_coverage_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
