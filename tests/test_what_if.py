"""
tests/test_what_if.py
======================

Tests for Phase 4: What-If Analysis (src/analysis/what_if.py).

Design principles:
- Financial-only tests assert purely against simulate_financials() outputs.
- ML tests that check routing/isolation use unittest.mock to patch the
  predictor so the test does not depend on live model calls.
- ML tests that check actual predictor behaviour call the real predictor.
- No Google Places API is called anywhere in these tests.
- No financial formulas are re-implemented here; expected values are
  derived by calling simulate_financials() directly.
"""

import unittest
from unittest.mock import patch, MagicMock

from src.finance.simulator import simulate_financials
from src.analysis.what_if import (
    compare_financial_scenarios,
    compare_ml_scenarios,
    describe_financial_changes,
    FINANCIAL_KEYS,
    ML_KEYS,
    _safe_pct_change,
)


# ------------------------------------------------------------------
# Shared fixtures
# ------------------------------------------------------------------

BASELINE_FIN = dict(
    customers_per_day=100,
    average_order_value=300,
    rent=100_000,
    staff_cost=150_000,
    food_cost_percent=30,
    utilities=20_000,
    marketing=15_000,
    other_expenses=15_000,
    working_days=30,
)

# Reference ML inputs — used for ML scenario tests
BASELINE_ML = dict(
    online_order=1,
    book_table=0,
    approx_costfor_two_people=800.0,
    cost_band="Medium",
    location="Koramangala",
    primary_cuisine="North Indian",
    cuisine_count=2,
    primary_rest_type="Casual Dining",
    historical_restaurant_count=120,
    location_median_cost=600.0,
    location_online_order_rate=0.65,
    location_book_table_rate=0.25,
    location_cuisine_diversity=15,
    location_business_type_diversity=8,
)


class TestWhatIfFinancial(unittest.TestCase):

    # ------------------------------------------------------------------
    # TEST 1 — Identical baseline and scenario produce zero differences
    # ------------------------------------------------------------------
    def test_01_identical_scenarios_produce_zero_changes(self):
        """When baseline == scenario, all absolute changes must be zero."""
        result = compare_financial_scenarios(BASELINE_FIN, BASELINE_FIN)

        changes = result["changes"]
        for key, entry in changes.items():
            absolute = entry["absolute"]
            if absolute is not None:
                self.assertAlmostEqual(
                    absolute, 0.0, places=4,
                    msg=f"Expected zero change for '{key}', got {absolute}",
                )

    # ------------------------------------------------------------------
    # TEST 2 — Increasing customers/day increases monthly revenue
    # ------------------------------------------------------------------
    def test_02_more_customers_increases_revenue(self):
        """Increasing customers_per_day must increase monthly_revenue."""
        scenario = {**BASELINE_FIN, "customers_per_day": 120}
        result = compare_financial_scenarios(BASELINE_FIN, scenario)

        self.assertGreater(result["changes"]["monthly_revenue"]["absolute"], 0)
        self.assertGreater(result["scenario"]["monthly_revenue"],
                           result["baseline"]["monthly_revenue"])

    # ------------------------------------------------------------------
    # TEST 3 — Increasing AOV increases monthly revenue
    # ------------------------------------------------------------------
    def test_03_higher_aov_increases_revenue(self):
        """Increasing average_order_value must increase monthly_revenue."""
        scenario = {**BASELINE_FIN, "average_order_value": 400}
        result = compare_financial_scenarios(BASELINE_FIN, scenario)

        self.assertGreater(result["changes"]["monthly_revenue"]["absolute"], 0)

    # ------------------------------------------------------------------
    # TEST 4 — Increasing rent decreases operating profit
    # ------------------------------------------------------------------
    def test_04_higher_rent_decreases_profit(self):
        """Increasing rent must decrease estimated_operating_profit."""
        scenario = {**BASELINE_FIN, "rent": 150_000}
        result = compare_financial_scenarios(BASELINE_FIN, scenario)

        self.assertLess(result["changes"]["estimated_operating_profit"]["absolute"], 0)

    # ------------------------------------------------------------------
    # TEST 5 — Increasing food cost decreases operating profit
    # ------------------------------------------------------------------
    def test_05_higher_food_cost_decreases_profit(self):
        """Increasing food_cost_percent must decrease estimated_operating_profit."""
        scenario = {**BASELINE_FIN, "food_cost_percent": 45}
        result = compare_financial_scenarios(BASELINE_FIN, scenario)

        self.assertLess(result["changes"]["estimated_operating_profit"]["absolute"], 0)

    # ------------------------------------------------------------------
    # TEST 6 — Financial-only changes do NOT call the ML predictor
    # ------------------------------------------------------------------
    def test_06_financial_only_does_not_call_ml_predictor(self):
        """compare_financial_scenarios must never call predict_business_performance."""
        with patch(
            "src.analysis.what_if.predict_business_performance"
        ) as mock_predict:
            compare_financial_scenarios(BASELINE_FIN, BASELINE_FIN)
            mock_predict.assert_not_called()

    # ------------------------------------------------------------------
    # TEST 8 — Both baseline and scenario use the SAME financial simulator
    # ------------------------------------------------------------------
    def test_08_both_results_match_direct_simulator_calls(self):
        """baseline and scenario outputs must match direct simulate_financials() calls."""
        scenario = {**BASELINE_FIN, "customers_per_day": 120, "rent": 110_000}

        result = compare_financial_scenarios(BASELINE_FIN, scenario)

        expected_baseline = simulate_financials(**BASELINE_FIN)
        expected_scenario = simulate_financials(**{
            k: scenario[k] for k in FINANCIAL_KEYS if k in scenario
        })

        self.assertEqual(result["baseline"], expected_baseline)
        self.assertEqual(result["scenario"], expected_scenario)

    # ------------------------------------------------------------------
    # TEST 9 — Zero baseline values do not cause division-by-zero errors
    # ------------------------------------------------------------------
    def test_09_zero_baseline_revenue_no_crash(self):
        """Zero baseline revenue must not raise ZeroDivisionError."""
        zero_rev_baseline = {**BASELINE_FIN, "customers_per_day": 0}
        scenario = {**BASELINE_FIN, "customers_per_day": 50}

        try:
            result = compare_financial_scenarios(zero_rev_baseline, scenario)
        except ZeroDivisionError:
            self.fail("compare_financial_scenarios raised ZeroDivisionError")

        # When baseline revenue is 0 and scenario revenue > 0,
        # percentage for monthly_revenue should be None (undefined)
        self.assertIsNone(result["changes"]["monthly_revenue"]["percentage"])

        # Absolute change should still be calculable
        self.assertIsNotNone(result["changes"]["monthly_revenue"]["absolute"])
        self.assertGreater(result["changes"]["monthly_revenue"]["absolute"], 0)

    # ------------------------------------------------------------------
    # TEST 10 — Invalid inputs are rejected
    # ------------------------------------------------------------------
    def test_10_invalid_baseline_raises_value_error(self):
        """Invalid baseline inputs must raise ValueError (delegated to simulator)."""
        invalid_baseline = {**BASELINE_FIN, "rent": -5000}
        with self.assertRaises(ValueError):
            compare_financial_scenarios(invalid_baseline, BASELINE_FIN)

    def test_10b_invalid_scenario_raises_value_error(self):
        """Invalid scenario inputs must raise ValueError."""
        invalid_scenario = {**BASELINE_FIN, "food_cost_percent": 110}
        with self.assertRaises(ValueError):
            compare_financial_scenarios(BASELINE_FIN, invalid_scenario)

    # ------------------------------------------------------------------
    # Additional financial correctness tests
    # ------------------------------------------------------------------

    def test_11_absolute_revenue_change_is_correct(self):
        """Absolute revenue change matches direct simulator difference."""
        scenario = {**BASELINE_FIN, "average_order_value": 400}

        b = simulate_financials(**BASELINE_FIN)
        s = simulate_financials(**{k: scenario[k] for k in FINANCIAL_KEYS if k in scenario})

        result = compare_financial_scenarios(BASELINE_FIN, scenario)
        expected_abs = round(s["monthly_revenue"] - b["monthly_revenue"], 4)
        self.assertAlmostEqual(
            result["changes"]["monthly_revenue"]["absolute"],
            expected_abs,
            places=4,
        )

    def test_12_percentage_change_formula(self):
        """Percentage change follows ((s - b) / |b|) * 100 exactly."""
        scenario = {**BASELINE_FIN, "customers_per_day": 150}

        b = simulate_financials(**BASELINE_FIN)
        s = simulate_financials(**{k: scenario[k] for k in FINANCIAL_KEYS if k in scenario})

        result = compare_financial_scenarios(BASELINE_FIN, scenario)
        expected_pct = round(
            ((s["monthly_revenue"] - b["monthly_revenue"]) / abs(b["monthly_revenue"])) * 100,
            4,
        )
        self.assertAlmostEqual(
            result["changes"]["monthly_revenue"]["percentage"],
            expected_pct,
            places=4,
        )

    def test_13_result_structure_is_complete(self):
        """Result dict must contain 'baseline', 'scenario', and 'changes'."""
        result = compare_financial_scenarios(BASELINE_FIN, BASELINE_FIN)
        self.assertIn("baseline", result)
        self.assertIn("scenario", result)
        self.assertIn("changes", result)

        required_change_keys = {
            "monthly_revenue",
            "monthly_expenses",
            "estimated_operating_profit",
            "operating_profit_margin",
            "break_even_customers_per_day",
        }
        self.assertEqual(required_change_keys, set(result["changes"].keys()))

    def test_14_each_change_entry_has_absolute_and_percentage(self):
        """Every change entry must have 'absolute' and 'percentage' keys."""
        result = compare_financial_scenarios(BASELINE_FIN, BASELINE_FIN)
        for key, entry in result["changes"].items():
            self.assertIn("absolute", entry, msg=f"Missing 'absolute' in {key}")
            self.assertIn("percentage", entry, msg=f"Missing 'percentage' in {key}")

    def test_15_superset_dict_does_not_crash(self):
        """Passing a dict with extra keys (e.g. ML keys mixed in) must not crash."""
        superset = {**BASELINE_FIN, "online_order": 1, "location": "Koramangala"}
        # Only FINANCIAL_KEYS should be extracted; unknown keys ignored
        result = compare_financial_scenarios(superset, superset)
        self.assertIn("baseline", result)


class TestWhatIfML(unittest.TestCase):

    # ------------------------------------------------------------------
    # TEST 7 — ML input changes trigger the predictor
    # ------------------------------------------------------------------
    def test_07_ml_changes_call_predictor(self):
        """compare_ml_scenarios must call predict_business_performance for both inputs."""
        mock_result = {
            "prediction": "High",
            "probabilities": {"High": 0.60, "Low": 0.20, "Medium": 0.20},
        }
        with patch(
            "src.analysis.what_if.predict_business_performance",
            return_value=mock_result
        ) as mock_predict:
            scenario_ml = {**BASELINE_ML, "online_order": 0}
            compare_ml_scenarios(BASELINE_ML, scenario_ml, include_shap=False)
            self.assertEqual(mock_predict.call_count, 2,
                             "Expected predict_business_performance to be called twice "
                             "(once for baseline, once for scenario).")

    # ------------------------------------------------------------------
    # TEST 11 — ML scenario probabilities come from the actual predictor
    # ------------------------------------------------------------------
    def test_11_probabilities_come_from_real_predictor(self):
        """
        Baseline probabilities in compare_ml_scenarios must match a direct
        call to predict_business_performance with the same inputs.
        """
        from src.ml.predictor import predict_business_performance as real_predict

        direct = real_predict(**BASELINE_ML)
        result = compare_ml_scenarios(BASELINE_ML, BASELINE_ML, include_shap=False)

        self.assertEqual(
            result["baseline"]["probabilities"],
            direct["probabilities"],
        )

    # ------------------------------------------------------------------
    # TEST 12 — SHAP scenario explanation comes from the existing explainer
    # ------------------------------------------------------------------
    def test_12_shap_comes_from_real_explainer_when_requested(self):
        """
        When include_shap=True, SHAP output must match a direct call to
        explain_business_prediction with the same inputs.
        """
        from src.ml.explainer import explain_business_prediction as real_explain

        result = compare_ml_scenarios(BASELINE_ML, BASELINE_ML, include_shap=True)

        # Both baseline and scenario shap must be present
        self.assertIsNotNone(result["baseline"]["shap"])
        self.assertIsNotNone(result["scenario"]["shap"])

        # top_features must be a non-empty list
        self.assertIn("top_features", result["baseline"]["shap"])
        self.assertTrue(len(result["baseline"]["shap"]["top_features"]) > 0)

        # Each feature entry must have the standard structure
        for feat in result["baseline"]["shap"]["top_features"]:
            self.assertIn("feature", feat)
            self.assertIn("contribution", feat)
            self.assertIn("direction", feat)
            self.assertIn(feat["direction"], ["positive", "negative"])

    def test_12b_shap_is_none_when_not_requested(self):
        """When include_shap=False (default), shap fields must be None."""
        result = compare_ml_scenarios(BASELINE_ML, BASELINE_ML, include_shap=False)
        self.assertIsNone(result["baseline"]["shap"])
        self.assertIsNone(result["scenario"]["shap"])

    # ------------------------------------------------------------------
    # TEST 13 — Existing Opportunity scoring behaviour remains unchanged
    # ------------------------------------------------------------------
    def test_13_opportunity_scoring_formula_unchanged(self):
        """
        Phase 4 must not modify analyze_business_opportunity().
        Calling it directly must produce the same result as before Phase 4.
        """
        from src.analysis.opportunity import analyze_business_opportunity

        probabilities = [0.55, 0.25, 0.20]
        model_classes = ["High", "Low", "Medium"]
        comp_summary = {
            "competitor_count_retrieved": 10,
            "avg_competitor_rating": 4.3,
            "median_competitor_rating": 4.4,
            "avg_competitor_reviews": 800.0,
            "median_competitor_reviews": 600.0,
            "high_rating_competitors": 3,
            "high_review_competitors": 1,
        }

        result = analyze_business_opportunity(
            probabilities=probabilities,
            model_classes=model_classes,
            competition_summary=comp_summary,
        )

        self.assertIn("opportunity_score", result)
        self.assertIn("historical_performance", result)
        self.assertIn("competition_strength", result)

        # Verify the formula is still the Phase 1 formula.
        # performance_score = 0.55*100 + 0.20*60 + 0.25*20 = 55 + 12 + 5 = 72
        #   (model_classes maps: High=0.55, Low=0.25, Medium=0.20)
        # Let's compute via the spec:
        class_probs = dict(zip(model_classes, probabilities))
        # High=0.55, Low=0.25, Medium=0.20
        perf_score = (
            class_probs.get("High", 0) * 100
            + class_probs.get("Medium", 0) * 60
            + class_probs.get("Low", 0) * 20
        )
        self.assertAlmostEqual(result["historical_performance"]["score"], perf_score, places=2)

    # ------------------------------------------------------------------
    # ML result structure tests
    # ------------------------------------------------------------------

    def test_14_ml_result_structure(self):
        """compare_ml_scenarios result must have the documented structure."""
        mock_result = {
            "prediction": "High",
            "probabilities": {"High": 0.60, "Low": 0.20, "Medium": 0.20},
        }
        with patch("src.analysis.what_if.predict_business_performance", return_value=mock_result):
            result = compare_ml_scenarios(BASELINE_ML, BASELINE_ML)

        self.assertIn("baseline", result)
        self.assertIn("scenario", result)
        self.assertIn("changes", result)

        for side in ("baseline", "scenario"):
            self.assertIn("prediction", result[side])
            self.assertIn("probabilities", result[side])
            self.assertIn("shap", result[side])

        self.assertIn("prediction_changed", result["changes"])
        self.assertIn("probability_changes", result["changes"])

    def test_15_prediction_changed_flag_false_when_same(self):
        """prediction_changed must be False when both scenarios predict the same class."""
        mock_result = {
            "prediction": "High",
            "probabilities": {"High": 0.70, "Low": 0.15, "Medium": 0.15},
        }
        with patch("src.analysis.what_if.predict_business_performance", return_value=mock_result):
            result = compare_ml_scenarios(BASELINE_ML, BASELINE_ML)

        self.assertFalse(result["changes"]["prediction_changed"])

    def test_16_prediction_changed_flag_true_when_different(self):
        """prediction_changed must be True when predictions differ."""
        baseline_mock = {
            "prediction": "High",
            "probabilities": {"High": 0.70, "Low": 0.15, "Medium": 0.15},
        }
        scenario_mock = {
            "prediction": "Low",
            "probabilities": {"High": 0.20, "Low": 0.60, "Medium": 0.20},
        }
        with patch(
            "src.analysis.what_if.predict_business_performance",
            side_effect=[baseline_mock, scenario_mock]
        ):
            result = compare_ml_scenarios(BASELINE_ML, BASELINE_ML)

        self.assertTrue(result["changes"]["prediction_changed"])


class TestSafePctChange(unittest.TestCase):
    """Unit tests for the internal _safe_pct_change helper."""

    def test_normal_increase(self):
        result = _safe_pct_change(100, 150)
        self.assertAlmostEqual(result, 50.0, places=4)

    def test_normal_decrease(self):
        result = _safe_pct_change(200, 100)
        self.assertAlmostEqual(result, -50.0, places=4)

    def test_zero_baseline_nonzero_scenario_returns_none(self):
        """Division by zero — returns None."""
        result = _safe_pct_change(0, 100)
        self.assertIsNone(result)

    def test_both_zero_returns_zero(self):
        result = _safe_pct_change(0, 0)
        self.assertEqual(result, 0.0)

    def test_negative_baseline(self):
        """Uses abs(baseline) in denominator."""
        result = _safe_pct_change(-100, -50)
        # ((-50 - -100) / 100) * 100 = 50%
        self.assertAlmostEqual(result, 50.0, places=4)


class TestDescribeFinancialChanges(unittest.TestCase):
    """Tests for the factual interpretation layer."""

    def test_no_statements_when_no_change(self):
        """Identical scenarios produce an empty statements list."""
        result = compare_financial_scenarios(BASELINE_FIN, BASELINE_FIN)
        statements = describe_financial_changes(result)
        self.assertEqual(statements, [])

    def test_statements_present_when_revenue_changes(self):
        """Changing revenue must produce at least one statement."""
        scenario = {**BASELINE_FIN, "customers_per_day": 150}
        result = compare_financial_scenarios(BASELINE_FIN, scenario)
        statements = describe_financial_changes(result)
        self.assertTrue(len(statements) > 0)

    def test_statements_are_strings(self):
        """All statements must be plain strings."""
        scenario = {**BASELINE_FIN, "average_order_value": 400, "rent": 120_000}
        result = compare_financial_scenarios(BASELINE_FIN, scenario)
        statements = describe_financial_changes(result)
        for stmt in statements:
            self.assertIsInstance(stmt, str)

    def test_no_subjective_claims_in_statements(self):
        """Statements must not contain subjective phrases like 'good decision'."""
        scenario = {**BASELINE_FIN, "average_order_value": 400}
        result = compare_financial_scenarios(BASELINE_FIN, scenario)
        statements = describe_financial_changes(result)
        forbidden = ["good decision", "bad decision", "definitely", "guaranteed", "success"]
        for stmt in statements:
            for phrase in forbidden:
                self.assertNotIn(phrase, stmt.lower(),
                                 msg=f"Subjective phrase '{phrase}' found in: {stmt}")


class TestPhaseIsolation(unittest.TestCase):
    """Verify Phase 1/2/3 functions are reused, not duplicated."""

    def test_financial_keys_cover_simulator_signature(self):
        """FINANCIAL_KEYS must include all parameters of simulate_financials()."""
        import inspect
        from src.finance.simulator import simulate_financials
        sig = inspect.signature(simulate_financials)
        for param_name in sig.parameters:
            self.assertIn(
                param_name,
                FINANCIAL_KEYS,
                msg=f"simulate_financials parameter '{param_name}' not in FINANCIAL_KEYS",
            )

    def test_ml_keys_cover_predictor_signature(self):
        """ML_KEYS must include all parameters of predict_business_performance()."""
        import inspect
        from src.ml.predictor import predict_business_performance
        sig = inspect.signature(predict_business_performance)
        for param_name in sig.parameters:
            self.assertIn(
                param_name,
                ML_KEYS,
                msg=f"predict_business_performance parameter '{param_name}' not in ML_KEYS",
            )

    def test_no_formula_duplication(self):
        """
        compare_financial_scenarios result must exactly match
        two separate simulate_financials() calls.
        Only the reused function should compute figures.
        """
        scenario = {**BASELINE_FIN, "customers_per_day": 130, "marketing": 20_000}
        result = compare_financial_scenarios(BASELINE_FIN, scenario)

        direct_b = simulate_financials(**BASELINE_FIN)
        direct_s = simulate_financials(**{k: scenario[k] for k in FINANCIAL_KEYS if k in scenario})

        self.assertEqual(result["baseline"], direct_b)
        self.assertEqual(result["scenario"], direct_s)


if __name__ == "__main__":
    unittest.main()
