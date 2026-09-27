import unittest
import asyncio
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

from src.agent.location_agent import location_agent, location_analysis_tool
from src.agent.performance_agent import performance_agent, performance_analysis_tool
from src.agent.competition_agent import competition_agent, competition_analysis_tool
from src.agent.opportunity_agent import opportunity_agent, opportunity_analysis_tool
from src.agent.coordinator_agent import coordinator_agent, run_full_business_analysis


class MockToolContext:
    def __init__(self):
        self.state = {}


class TestADKOrchestration(unittest.TestCase):

    def test_state_handoff_between_tools(self):
        """
        Verify that ToolContext state reliably caches location, performance, and
        competition outputs and feeds them directly into opportunity_analysis_tool.
        The competition_result stored in state must have all required keys.
        """
        ctx = MockToolContext()

        # Step 1: Location Tool
        loc_res = location_analysis_tool(location="Koramangala", tool_context=ctx)
        self.assertIn("location_result", ctx.state)
        self.assertTrue(ctx.state["location_result"]["found"])

        # Step 2: Performance Tool (uses location_result from state automatically if omitted)
        perf_res = performance_analysis_tool(
            online_order=1,
            book_table=0,
            approx_costfor_two_people=700.0,
            cost_band="Medium",
            location="Koramangala",
            primary_cuisine="Japanese",
            cuisine_count=2,
            primary_rest_type="Casual Dining",
            tool_context=ctx
        )
        self.assertIn("performance_result", ctx.state)
        self.assertIn("explanation", perf_res)

        # Step 3: Competition output stored in state with ALL required keys
        comp_summary = {
            "competitor_count_retrieved": 8,
            "avg_competitor_rating": 4.25,
            "median_competitor_rating": 4.3,
            "avg_competitor_reviews": 500.0,
            "median_competitor_reviews": 400.0,
            "high_rating_competitors": 2,
            "high_review_competitors": 1
        }
        ctx.state["competition_result"] = comp_summary

        # Step 4: Opportunity Tool called without arguments (reads state)
        opp_res = opportunity_analysis_tool(tool_context=ctx)
        self.assertIn("opportunity_result", ctx.state)
        self.assertIn("opportunity_score", opp_res)
        self.assertGreater(opp_res["opportunity_score"]["score"], 0)

    def test_opportunity_raises_when_performance_missing_from_state(self):
        """
        Verify that opportunity_analysis_tool raises ValueError when neither
        explicit probabilities nor performance_result in state are available.
        """
        ctx = MockToolContext()

        # Only competition_result in state — no performance
        ctx.state["competition_result"] = {
            "competitor_count_retrieved": 5,
            "avg_competitor_rating": 4.1,
            "median_competitor_rating": 4.0,
            "avg_competitor_reviews": 300.0,
            "median_competitor_reviews": 250.0,
            "high_rating_competitors": 1,
            "high_review_competitors": 0
        }

        with self.assertRaises(ValueError) as ctx_mgr:
            opportunity_analysis_tool(tool_context=ctx)
        self.assertIn("Performance Agent output is required", str(ctx_mgr.exception))

    def test_opportunity_raises_when_competition_missing_from_state(self):
        """
        Verify that opportunity_analysis_tool raises ValueError when neither
        explicit competition_summary nor competition_result in state are available.
        """
        ctx = MockToolContext()

        # Populate state with valid performance data
        ctx.state["performance_result"] = {
            "probabilities": {"High": 0.55, "Low": 0.20, "Medium": 0.25},
            "prediction": "High"
        }
        # No competition_result in state

        with self.assertRaises(ValueError) as ctx_mgr:
            opportunity_analysis_tool(tool_context=ctx)
        self.assertIn("Competition Agent output is required", str(ctx_mgr.exception))

    def test_opportunity_raises_when_state_competition_has_incomplete_keys(self):
        """
        Verify that opportunity_analysis_tool raises ValueError when competition_result
        in state is missing required keys (e.g., stored with non-canonical names).
        """
        ctx = MockToolContext()

        ctx.state["performance_result"] = {
            "probabilities": {"High": 0.55, "Low": 0.20, "Medium": 0.25},
            "prediction": "High"
        }
        # competition_result with wrong / missing keys
        ctx.state["competition_result"] = {
            "competitor_count": 5,  # wrong key — should be competitor_count_retrieved
            "avg_rating": 4.1        # wrong key — should be avg_competitor_rating
        }

        with self.assertRaises(ValueError) as ctx_mgr:
            opportunity_analysis_tool(tool_context=ctx)
        self.assertIn("missing required keys", str(ctx_mgr.exception))

    def test_coordinator_agent_structure(self):
        """
        Verify Coordinator Agent contains the four required specialized AgentTools
        plus the run_full_business_analysis orchestration function.
        """
        self.assertEqual(coordinator_agent.name, "coordinator_agent")
        tool_names = [t.name if hasattr(t, 'name') else t.__name__ for t in coordinator_agent.tools]

        # Four individual AgentTools
        self.assertIn("location_agent", tool_names)
        self.assertIn("performance_agent", tool_names)
        self.assertIn("competition_agent", tool_names)
        self.assertIn("opportunity_agent", tool_names)

        # Python-level orchestration function that guarantees ordering
        self.assertIn("run_full_business_analysis", tool_names)

        # Total: 4 AgentTools + 1 orchestration function
        self.assertEqual(len(coordinator_agent.tools), 5)

    def test_run_full_business_analysis_sequencing(self):
        """
        Verify run_full_business_analysis populates all four result keys in ToolContext
        state in the correct order. Opportunity result must be present only after
        Performance and Competition results are already stored.
        """
        ctx = MockToolContext()
        order_log = []

        # Patch tool functions to track execution order
        import src.agent.coordinator_agent as coord_mod
        original_loc = coord_mod.location_analysis_tool
        original_perf = coord_mod.performance_analysis_tool
        original_comp = coord_mod.competition_analysis_tool
        original_opp = coord_mod.opportunity_analysis_tool

        def mock_loc(**kwargs):
            order_log.append("location")
            return original_loc(**kwargs)

        def mock_perf(**kwargs):
            order_log.append("performance")
            return original_perf(**kwargs)

        def mock_comp(**kwargs):
            order_log.append("competition")
            # competition_analysis_tool makes a live Google Places call; return
            # a synthetic result so this test does not require network access.
            result = {
                "competition_summary": {
                    "competitor_count_retrieved": 4,
                    "avg_competitor_rating": 4.2,
                    "median_competitor_rating": 4.2,
                    "avg_competitor_reviews": 350.0,
                    "median_competitor_reviews": 300.0,
                    "high_rating_competitors": 1,
                    "high_review_competitors": 0
                },
                "competitors": []
            }
            if kwargs.get("tool_context") and hasattr(kwargs["tool_context"], "state"):
                kwargs["tool_context"].state["competition_result"] = result["competition_summary"]
                kwargs["tool_context"].state["full_competition_result"] = result
            return result

        def mock_opp(**kwargs):
            # Opportunity must only run AFTER performance and competition
            self.assertIn("performance", order_log,
                          "Opportunity ran before Performance was recorded.")
            self.assertIn("competition", order_log,
                          "Opportunity ran before Competition was recorded.")
            order_log.append("opportunity")
            return original_opp(**kwargs)

        coord_mod.location_analysis_tool = mock_loc
        coord_mod.performance_analysis_tool = mock_perf
        coord_mod.competition_analysis_tool = mock_comp
        coord_mod.opportunity_analysis_tool = mock_opp

        try:
            result = run_full_business_analysis(
                location="Koramangala",
                search_query="Japanese restaurants in Koramangala",
                online_order=1,
                book_table=0,
                approx_costfor_two_people=800.0,
                cost_band="Medium",
                primary_cuisine="Japanese",
                cuisine_count=2,
                primary_rest_type="Casual Dining",
                tool_context=ctx
            )
        finally:
            coord_mod.location_analysis_tool = original_loc
            coord_mod.performance_analysis_tool = original_perf
            coord_mod.competition_analysis_tool = original_comp
            coord_mod.opportunity_analysis_tool = original_opp

        # Confirm all four phases ran
        self.assertIn("location", order_log)
        self.assertIn("performance", order_log)
        self.assertIn("competition", order_log)
        self.assertIn("opportunity", order_log)

        # Confirm ordering: location before performance before competition before opportunity
        self.assertLess(order_log.index("location"), order_log.index("performance"))
        self.assertLess(order_log.index("performance"), order_log.index("opportunity"))
        self.assertLess(order_log.index("competition"), order_log.index("opportunity"))

        # Confirm all four result keys are returned
        self.assertIn("location_result", result)
        self.assertIn("performance_result", result)
        self.assertIn("competition_result", result)
        self.assertIn("opportunity_result", result)


if __name__ == "__main__":
    unittest.main()
