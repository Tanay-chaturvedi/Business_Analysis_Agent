import os
import unittest
import numpy as np
import pandas as pd

from src.analysis.location_context import get_location_context
from src.ml.predictor import predict_business_performance
from src.ml.explainer import explain_business_prediction
from src.places.competition import summarize_competition
from src.analysis.opportunity import analyze_business_opportunity

from src.agent.location_agent import location_analysis_tool, location_agent
from src.agent.performance_agent import performance_analysis_tool, performance_agent
from src.agent.competition_agent import competition_analysis_tool, competition_agent
from src.agent.opportunity_agent import opportunity_analysis_tool, opportunity_agent
from src.agent.coordinator_agent import coordinator_agent, run_full_business_analysis


class TestPhase1AndPhase2(unittest.TestCase):

    def test_1_competition_only_request(self):
        """
        TEST 1: Competition-only request.
        Confirm Competition Agent works independently and tools perform only competitor retrieval.
        """
        # Test direct tool call with dummy competitors or mock
        sample_competitors = pd.DataFrame([
            {
                "place_id": "p1",
                "name": "Cafe 1",
                "rating": 4.6,
                "review_count": 2500,
                "types": ["restaurant"],
                "latitude": 12.97,
                "longitude": 77.59
            }
        ])
        summary = summarize_competition(sample_competitors)
        self.assertIn("competitor_count_retrieved", summary)
        self.assertEqual(summary["competitor_count_retrieved"], 1)
        self.assertEqual(summary["high_rating_competitors"], 1)
        self.assertEqual(summary["high_review_competitors"], 1)

        # Verify competition_agent has ONLY competition_analysis_tool
        tool_names = [t.name if hasattr(t, 'name') else t.__name__ for t in competition_agent.tools]
        self.assertIn("competition_analysis_tool", tool_names)
        self.assertEqual(len(competition_agent.tools), 1)

    def test_2_location_only_request(self):
        """
        TEST 2: Location-only request.
        Confirm Location Agent works independently.
        """
        result = location_analysis_tool("Koramangala")
        self.assertTrue(result["found"])
        self.assertIn("historical_restaurant_count", result)
        self.assertIn("location_median_cost", result)

        tool_names = [t.name if hasattr(t, 'name') else t.__name__ for t in location_agent.tools]
        self.assertIn("location_analysis_tool", tool_names)
        self.assertEqual(len(location_agent.tools), 1)

    def test_3_performance_only_request(self):
        """
        TEST 3: Performance-only request.
        Confirm Performance Agent works independently and includes SHAP explanation.
        """
        result = performance_analysis_tool(
            online_order=1,
            book_table=0,
            approx_costfor_two_people=800.0,
            cost_band="Medium",
            location="Koramangala",
            primary_cuisine="Japanese",
            cuisine_count=2,
            primary_rest_type="Casual Dining"
        )
        self.assertIn("prediction", result)
        self.assertIn("probabilities", result)
        self.assertIn("explanation", result)
        self.assertIn("top_features", result["explanation"])
        self.assertTrue(len(result["explanation"]["top_features"]) > 0)

        tool_names = [t.name if hasattr(t, 'name') else t.__name__ for t in performance_agent.tools]
        self.assertIn("performance_analysis_tool", tool_names)
        self.assertEqual(len(performance_agent.tools), 1)

    def test_4_opportunity_full_analysis(self):
        """
        TEST 4: Opportunity/full-analysis request.
        Confirm structured handoff to Opportunity Agent without KeyError.
        Only accepts real, complete Performance and Competition data.
        """
        perf_res = performance_analysis_tool(
            online_order=1,
            book_table=1,
            approx_costfor_two_people=1000.0,
            cost_band="Upper-Mid",
            location="Koramangala",
            primary_cuisine="Japanese",
            cuisine_count=3,
            primary_rest_type="Casual Dining"
        )

        comp_summary = {
            "competitor_count_retrieved": 10,
            "avg_competitor_rating": 4.3,
            "median_competitor_rating": 4.4,
            "avg_competitor_reviews": 800.0,
            "median_competitor_reviews": 600.0,
            "high_rating_competitors": 3,
            "high_review_competitors": 1
        }

        # Opportunity tool execution with valid, complete inputs
        opp_res = opportunity_analysis_tool(
            probabilities=perf_res["probabilities"],
            model_classes=list(perf_res["probabilities"].keys()),
            competition_summary=comp_summary
        )

        self.assertIn("opportunity_score", opp_res)
        self.assertIn("historical_performance", opp_res)
        self.assertIn("competition_strength", opp_res)
        self.assertIsInstance(opp_res["opportunity_score"]["score"], float)

    def test_4b_opportunity_raises_on_missing_performance(self):
        """
        TEST 4b: Opportunity must raise ValueError when probabilities are missing.
        Do NOT fabricate missing Performance Agent data.
        """
        comp_summary = {
            "competitor_count_retrieved": 10,
            "avg_competitor_rating": 4.3,
            "median_competitor_rating": 4.4,
            "avg_competitor_reviews": 800.0,
            "median_competitor_reviews": 600.0,
            "high_rating_competitors": 3,
            "high_review_competitors": 1
        }

        with self.assertRaises(ValueError) as ctx:
            opportunity_analysis_tool(
                probabilities=None,
                model_classes=None,
                competition_summary=comp_summary
            )
        self.assertIn("Performance Agent output is required", str(ctx.exception))

    def test_4c_opportunity_raises_on_missing_competition_summary(self):
        """
        TEST 4c: Opportunity must raise ValueError when competition_summary is missing.
        Do NOT fabricate missing Competition Agent data.
        """
        with self.assertRaises(ValueError) as ctx:
            opportunity_analysis_tool(
                probabilities={"High": 0.6, "Low": 0.2, "Medium": 0.2},
                model_classes=["High", "Low", "Medium"],
                competition_summary=None
            )
        self.assertIn("Competition Agent output is required", str(ctx.exception))

    def test_4d_opportunity_raises_on_incomplete_competition_summary(self):
        """
        TEST 4d: Opportunity must raise ValueError when competition_summary is missing keys.
        Do NOT silently convert missing keys to zero or rename them.
        """
        # Partial summary using non-canonical key names (competitor_count, avg_rating)
        partial_summary = {
            "competitor_count": 5,
            "avg_rating": 4.2
        }

        with self.assertRaises(ValueError) as ctx:
            opportunity_analysis_tool(
                probabilities={"High": 0.6, "Low": 0.2, "Medium": 0.2},
                model_classes=["High", "Low", "Medium"],
                competition_summary=partial_summary
            )
        self.assertIn("missing required keys", str(ctx.exception))

    def test_4e_opportunity_raises_on_empty_probabilities_list(self):
        """
        TEST 4e: Opportunity must raise ValueError when probabilities is an empty list.
        """
        comp_summary = {
            "competitor_count_retrieved": 5,
            "avg_competitor_rating": 4.2,
            "median_competitor_rating": 4.1,
            "avg_competitor_reviews": 300.0,
            "median_competitor_reviews": 250.0,
            "high_rating_competitors": 1,
            "high_review_competitors": 0
        }

        with self.assertRaises(ValueError):
            opportunity_analysis_tool(
                probabilities=[],
                model_classes=["High", "Low", "Medium"],
                competition_summary=comp_summary
            )

    def test_5_shap_explainability(self):
        """
        TEST 5: SHAP explainability verification.
        Verify prediction, probabilities, SHAP values, feature names, directions, top features.
        """
        exp = explain_business_prediction(
            online_order=1,
            book_table=0,
            approx_costfor_two_people=800.0,
            cost_band="Medium",
            location="Koramangala",
            primary_cuisine="Japanese",
            cuisine_count=2,
            primary_rest_type="Casual Dining",
            historical_restaurant_count=120,
            location_median_cost=600.0,
            location_online_order_rate=0.65,
            location_book_table_rate=0.25,
            location_cuisine_diversity=15,
            location_business_type_diversity=8,
            top_n=5
        )

        self.assertIn("prediction", exp)
        self.assertIn("top_features", exp)
        self.assertEqual(len(exp["top_features"]), 5)

        for feat in exp["top_features"]:
            self.assertIn("feature", feat)
            self.assertIn("contribution", feat)
            self.assertIn("direction", feat)
            self.assertIn(feat["direction"], ["positive", "negative"])
            self.assertIsInstance(feat["contribution"], float)

    def test_6_regression_check(self):
        """
        TEST 6: Regression check.
        Confirm original predict_business_performance behavior and outputs remain untouched.
        """
        raw_pred = predict_business_performance(
            online_order=1,
            book_table=0,
            approx_costfor_two_people=800.0,
            cost_band="Medium",
            location="Koramangala",
            primary_cuisine="Japanese",
            cuisine_count=2,
            primary_rest_type="Casual Dining",
            historical_restaurant_count=120,
            location_median_cost=600.0,
            location_online_order_rate=0.65,
            location_book_table_rate=0.25,
            location_cuisine_diversity=15,
            location_business_type_diversity=8
        )

        self.assertIn("prediction", raw_pred)
        self.assertIn("probabilities", raw_pred)
        self.assertEqual(set(raw_pred["probabilities"].keys()), {"High", "Low", "Medium"})
        prob_sum = sum(raw_pred["probabilities"].values())
        self.assertAlmostEqual(prob_sum, 1.0, places=2)

    def test_7_coordinator_has_independent_agents_and_orchestrator(self):
        """
        TEST 7: Coordinator structure verification.
        Must have all four individual AgentTools plus run_full_business_analysis.
        """
        tool_names = [t.name if hasattr(t, 'name') else t.__name__ for t in coordinator_agent.tools]

        # Independent per-agent tools must be present
        self.assertIn("location_agent", tool_names)
        self.assertIn("performance_agent", tool_names)
        self.assertIn("competition_agent", tool_names)
        self.assertIn("opportunity_agent", tool_names)

        # Python-level orchestrator must be present
        self.assertIn("run_full_business_analysis", tool_names)

        # Total: 4 AgentTools + 1 orchestration function
        self.assertEqual(len(coordinator_agent.tools), 5)


if __name__ == "__main__":
    unittest.main()
