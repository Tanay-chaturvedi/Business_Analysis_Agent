"""
tests/test_financial_simulator.py
==================================

Tests for Phase 3: Financial Simulator (src/finance/simulator.py).

Every expected value is derived from the formula directly in the test,
so the assertions are self-documenting — no unexplained magic numbers.

Formulas under test:
    A) monthly_customers        = customers_per_day * working_days
    B) monthly_revenue          = monthly_customers * average_order_value
    C) food_cost                = monthly_revenue * (food_cost_percent / 100)
    D) fixed_costs              = rent + staff_cost + utilities + marketing + other_expenses
    E) monthly_expenses         = fixed_costs + food_cost
    F) estimated_operating_profit = monthly_revenue - monthly_expenses
    G) operating_profit_margin  = (estimated_operating_profit / monthly_revenue) * 100
    H) contribution_per_customer = average_order_value * (1 - food_cost_percent / 100)
    I) break_even_monthly       = fixed_costs / contribution_per_customer
    J) break_even_per_day       = break_even_monthly / working_days
"""

import unittest
from src.finance.simulator import simulate_financials


class TestFinancialSimulator(unittest.TestCase):

    # ------------------------------------------------------------------
    # Shared helper — reference scenario used across multiple tests
    # ------------------------------------------------------------------
    SCENARIO = dict(
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

    def _run_reference(self):
        return simulate_financials(**self.SCENARIO)

    # ==================================================================
    # TEST 1 — Normal profitable scenario
    # ==================================================================
    def test_01_normal_profitable_scenario(self):
        """Full scenario produces positive estimated operating profit."""
        result = self._run_reference()

        # Result keys must be present
        required_keys = {
            "monthly_customers",
            "monthly_revenue",
            "food_cost",
            "fixed_costs",
            "monthly_expenses",
            "estimated_operating_profit",
            "operating_profit_margin",
            "break_even_customers_per_day",
        }
        self.assertEqual(required_keys, set(result.keys()))

        # Profitable scenario should produce a positive operating profit
        self.assertGreater(result["estimated_operating_profit"], 0)

        # Margin must be positive and <= 100 %
        self.assertGreater(result["operating_profit_margin"], 0)
        self.assertLessEqual(result["operating_profit_margin"], 100)

    # ==================================================================
    # TEST 2 — Zero customers
    # ==================================================================
    def test_02_zero_customers(self):
        """Zero customers per day produces zero revenue and negative profit."""
        result = simulate_financials(
            customers_per_day=0,
            average_order_value=300,
            rent=100_000,
            staff_cost=150_000,
            food_cost_percent=30,
            utilities=20_000,
            marketing=15_000,
            other_expenses=15_000,
            working_days=30,
        )

        self.assertEqual(result["monthly_customers"], 0)
        self.assertEqual(result["monthly_revenue"], 0.0)
        self.assertEqual(result["food_cost"], 0.0)

        # All fixed costs still apply
        expected_fixed = 100_000 + 150_000 + 20_000 + 15_000 + 15_000
        self.assertEqual(result["fixed_costs"], expected_fixed)

        # Expenses = fixed costs only (food_cost is 0)
        self.assertEqual(result["monthly_expenses"], expected_fixed)

        # Operating profit is negative (only fixed costs, no revenue)
        self.assertEqual(result["estimated_operating_profit"], -expected_fixed)

        # Margin is 0 when revenue is 0
        self.assertEqual(result["operating_profit_margin"], 0.0)

    # ==================================================================
    # TEST 3 — Zero revenue (zero AOV)
    # ==================================================================
    def test_03_zero_average_order_value(self):
        """Zero average order value means zero revenue regardless of customers."""
        result = simulate_financials(
            customers_per_day=100,
            average_order_value=0,
            rent=50_000,
            staff_cost=80_000,
            food_cost_percent=30,
            utilities=10_000,
            marketing=5_000,
            other_expenses=5_000,
            working_days=30,
        )

        self.assertEqual(result["monthly_revenue"], 0.0)
        self.assertEqual(result["food_cost"], 0.0)
        self.assertEqual(result["operating_profit_margin"], 0.0)

        expected_fixed = 50_000 + 80_000 + 10_000 + 5_000 + 5_000
        self.assertLess(result["estimated_operating_profit"], 0)
        self.assertEqual(result["estimated_operating_profit"], -expected_fixed)

    # ==================================================================
    # TEST 4 — 0 % food cost
    # ==================================================================
    def test_04_zero_food_cost_percent(self):
        """0 % food cost means food_cost = 0; full revenue flows to cover fixed costs."""
        result = simulate_financials(
            customers_per_day=50,
            average_order_value=200,
            rent=40_000,
            staff_cost=60_000,
            food_cost_percent=0,
            utilities=8_000,
            marketing=4_000,
            other_expenses=4_000,
            working_days=30,
        )

        self.assertEqual(result["food_cost"], 0.0)

        monthly_customers = 50 * 30          # 1500
        monthly_revenue = 1500 * 200         # 300_000
        fixed_costs = 40_000 + 60_000 + 8_000 + 4_000 + 4_000  # 116_000
        monthly_expenses = fixed_costs       # food_cost is 0
        profit = monthly_revenue - monthly_expenses

        self.assertAlmostEqual(result["monthly_revenue"], monthly_revenue, places=2)
        self.assertAlmostEqual(result["monthly_expenses"], monthly_expenses, places=2)
        self.assertAlmostEqual(result["estimated_operating_profit"], profit, places=2)

        # Break-even: contribution_per_customer = AOV * 1 = 200
        # break_even_monthly = fixed / 200; per_day = / 30
        expected_bep = fixed_costs / 200 / 30
        self.assertIsNotNone(result["break_even_customers_per_day"])
        self.assertAlmostEqual(result["break_even_customers_per_day"], expected_bep, places=4)

    # ==================================================================
    # TEST 5 — 100 % food cost
    # ==================================================================
    def test_05_hundred_percent_food_cost(self):
        """100 % food cost means all revenue is consumed by variable cost.
        Contribution per customer = 0, so break-even is undefined (None).
        """
        result = simulate_financials(
            customers_per_day=100,
            average_order_value=300,
            rent=50_000,
            staff_cost=80_000,
            food_cost_percent=100,
            utilities=10_000,
            marketing=5_000,
            other_expenses=5_000,
            working_days=30,
        )

        monthly_customers = 100 * 30         # 3000
        monthly_revenue = 3000 * 300         # 900_000
        food_cost = monthly_revenue * 1.0    # 900_000

        self.assertAlmostEqual(result["food_cost"], food_cost, places=2)

        # Estimated operating profit = revenue - food_cost - fixed_costs
        fixed_costs = 50_000 + 80_000 + 10_000 + 5_000 + 5_000
        self.assertAlmostEqual(
            result["estimated_operating_profit"],
            monthly_revenue - food_cost - fixed_costs,
            places=2,
        )

        # Break-even is undefined when contribution = 0
        self.assertIsNone(result["break_even_customers_per_day"])

    # ==================================================================
    # TEST 6 — Negative input validation
    # ==================================================================
    def test_06_negative_input_raises(self):
        """Each negative numeric input must raise ValueError."""
        base = dict(
            customers_per_day=50,
            average_order_value=200,
            rent=40_000,
            staff_cost=60_000,
            food_cost_percent=30,
            utilities=8_000,
            marketing=4_000,
            other_expenses=4_000,
            working_days=30,
        )

        negative_fields = [
            "customers_per_day",
            "average_order_value",
            "rent",
            "staff_cost",
            "utilities",
            "marketing",
            "other_expenses",
        ]

        for field in negative_fields:
            kwargs = {**base, field: -1}
            with self.assertRaises(ValueError, msg=f"Expected ValueError for {field}=-1"):
                simulate_financials(**kwargs)

    # ==================================================================
    # TEST 7 — food_cost_percent > 100 validation
    # ==================================================================
    def test_07_food_cost_percent_above_100_raises(self):
        """food_cost_percent > 100 must raise ValueError."""
        with self.assertRaises(ValueError):
            simulate_financials(
                customers_per_day=100,
                average_order_value=300,
                rent=100_000,
                staff_cost=150_000,
                food_cost_percent=101,
                utilities=20_000,
                marketing=15_000,
                other_expenses=15_000,
            )

    # ==================================================================
    # TEST 8 — working_days <= 0 validation
    # ==================================================================
    def test_08_working_days_zero_raises(self):
        """working_days = 0 must raise ValueError."""
        with self.assertRaises(ValueError):
            simulate_financials(
                customers_per_day=100,
                average_order_value=300,
                rent=100_000,
                staff_cost=150_000,
                food_cost_percent=30,
                utilities=20_000,
                marketing=15_000,
                other_expenses=15_000,
                working_days=0,
            )

    def test_08b_working_days_negative_raises(self):
        """working_days < 0 must raise ValueError."""
        with self.assertRaises(ValueError):
            simulate_financials(
                customers_per_day=100,
                average_order_value=300,
                rent=100_000,
                staff_cost=150_000,
                food_cost_percent=30,
                utilities=20_000,
                marketing=15_000,
                other_expenses=15_000,
                working_days=-5,
            )

    # ==================================================================
    # TEST 9 — Break-even calculation correctness
    # ==================================================================
    def test_09_break_even_calculation(self):
        """Break-even customers per day follows formulas I and J exactly."""
        cpd = 100
        aov = 300
        food_pct = 30
        rent = 100_000
        staff = 150_000
        utilities = 20_000
        marketing = 15_000
        other = 15_000
        days = 30

        result = simulate_financials(
            customers_per_day=cpd,
            average_order_value=aov,
            rent=rent,
            staff_cost=staff,
            food_cost_percent=food_pct,
            utilities=utilities,
            marketing=marketing,
            other_expenses=other,
            working_days=days,
        )

        # H) contribution_per_customer
        contribution = aov * (1 - food_pct / 100)   # 300 * 0.70 = 210

        # D) fixed_costs
        fixed = rent + staff + utilities + marketing + other   # 300_000

        # I) break_even_monthly
        bep_monthly = fixed / contribution            # 300_000 / 210 ≈ 1428.5714

        # J) break_even_per_day
        bep_daily = bep_monthly / days                # ÷ 30 ≈ 47.619

        self.assertIsNotNone(result["break_even_customers_per_day"])
        self.assertAlmostEqual(
            result["break_even_customers_per_day"],
            round(bep_daily, 4),
            places=4,
        )

    # ==================================================================
    # TEST 10 — Zero contribution margin → break-even is None
    # ==================================================================
    def test_10_zero_contribution_margin_break_even_is_none(self):
        """When food_cost_percent = 100, contribution = 0, break-even = None."""
        result = simulate_financials(
            customers_per_day=80,
            average_order_value=250,
            rent=60_000,
            staff_cost=90_000,
            food_cost_percent=100,
            utilities=12_000,
            marketing=8_000,
            other_expenses=5_000,
            working_days=30,
        )
        self.assertIsNone(result["break_even_customers_per_day"])

    # ==================================================================
    # TEST 11 — Exact revenue formula verification
    # ==================================================================
    def test_11_exact_revenue_formula(self):
        """monthly_revenue = customers_per_day * working_days * average_order_value."""
        cpd, aov, days = 75, 400, 26
        result = simulate_financials(
            customers_per_day=cpd,
            average_order_value=aov,
            rent=50_000,
            staff_cost=70_000,
            food_cost_percent=25,
            utilities=8_000,
            marketing=5_000,
            other_expenses=5_000,
            working_days=days,
        )

        expected_revenue = cpd * days * aov            # 75 * 26 * 400 = 780_000
        self.assertEqual(result["monthly_customers"], cpd * days)
        self.assertAlmostEqual(result["monthly_revenue"], expected_revenue, places=2)

    # ==================================================================
    # TEST 12 — Exact expense formula verification
    # ==================================================================
    def test_12_exact_expense_formula(self):
        """monthly_expenses = fixed_costs + food_cost exactly."""
        cpd = 80
        aov = 350
        days = 28
        rent = 80_000
        staff = 120_000
        utilities = 15_000
        marketing = 10_000
        other = 10_000
        food_pct = 35

        result = simulate_financials(
            customers_per_day=cpd,
            average_order_value=aov,
            rent=rent,
            staff_cost=staff,
            food_cost_percent=food_pct,
            utilities=utilities,
            marketing=marketing,
            other_expenses=other,
            working_days=days,
        )

        monthly_revenue = cpd * days * aov             # 80 * 28 * 350 = 784_000
        food_cost = monthly_revenue * (food_pct / 100) # 784_000 * 0.35 = 274_400
        fixed = rent + staff + utilities + marketing + other  # 235_000
        expected_expenses = fixed + food_cost          # 509_400

        self.assertAlmostEqual(result["food_cost"], food_cost, places=2)
        self.assertAlmostEqual(result["fixed_costs"], fixed, places=2)
        self.assertAlmostEqual(result["monthly_expenses"], expected_expenses, places=2)

    # ==================================================================
    # TEST 13 — Exact operating profit formula verification
    # ==================================================================
    def test_13_exact_operating_profit_formula(self):
        """estimated_operating_profit = monthly_revenue - monthly_expenses exactly."""
        cpd = 120
        aov = 280
        days = 30
        rent = 90_000
        staff = 130_000
        utilities = 18_000
        marketing = 12_000
        other = 10_000
        food_pct = 28

        result = simulate_financials(
            customers_per_day=cpd,
            average_order_value=aov,
            rent=rent,
            staff_cost=staff,
            food_cost_percent=food_pct,
            utilities=utilities,
            marketing=marketing,
            other_expenses=other,
            working_days=days,
        )

        monthly_revenue = cpd * days * aov
        food_cost = monthly_revenue * (food_pct / 100)
        fixed = rent + staff + utilities + marketing + other
        monthly_expenses = fixed + food_cost
        expected_profit = monthly_revenue - monthly_expenses

        self.assertAlmostEqual(
            result["estimated_operating_profit"], expected_profit, places=2
        )

    # ==================================================================
    # TEST 14 — Exact operating margin formula verification
    # ==================================================================
    def test_14_exact_operating_margin_formula(self):
        """operating_profit_margin = (profit / revenue) * 100 exactly."""
        cpd = 100
        aov = 300
        days = 30
        rent = 100_000
        staff = 150_000
        utilities = 20_000
        marketing = 15_000
        other = 15_000
        food_pct = 30

        result = simulate_financials(
            customers_per_day=cpd,
            average_order_value=aov,
            rent=rent,
            staff_cost=staff,
            food_cost_percent=food_pct,
            utilities=utilities,
            marketing=marketing,
            other_expenses=other,
            working_days=days,
        )

        monthly_revenue = cpd * days * aov              # 900_000
        food_cost = monthly_revenue * (food_pct / 100)  # 270_000
        fixed = rent + staff + utilities + marketing + other  # 300_000
        monthly_expenses = fixed + food_cost             # 570_000
        profit = monthly_revenue - monthly_expenses      # 330_000
        expected_margin = (profit / monthly_revenue) * 100   # 36.666...%

        self.assertAlmostEqual(
            result["operating_profit_margin"], round(expected_margin, 4), places=4
        )

    # ==================================================================
    # Additional edge-case tests
    # ==================================================================

    def test_15_food_cost_percent_exactly_zero_is_valid(self):
        """food_cost_percent = 0 must not raise."""
        result = simulate_financials(
            customers_per_day=50,
            average_order_value=200,
            rent=30_000,
            staff_cost=50_000,
            food_cost_percent=0,
            utilities=5_000,
            marketing=3_000,
            other_expenses=2_000,
            working_days=30,
        )
        self.assertEqual(result["food_cost"], 0.0)

    def test_16_food_cost_percent_exactly_100_is_valid(self):
        """food_cost_percent = 100 must not raise (edge of valid range)."""
        result = simulate_financials(
            customers_per_day=50,
            average_order_value=200,
            rent=30_000,
            staff_cost=50_000,
            food_cost_percent=100,
            utilities=5_000,
            marketing=3_000,
            other_expenses=2_000,
            working_days=30,
        )
        # food_cost == monthly_revenue
        self.assertAlmostEqual(result["food_cost"], result["monthly_revenue"], places=2)
        self.assertIsNone(result["break_even_customers_per_day"])

    def test_17_all_fixed_costs_zero(self):
        """When all fixed costs are zero, break-even = 0 and profit equals margin."""
        result = simulate_financials(
            customers_per_day=100,
            average_order_value=300,
            rent=0,
            staff_cost=0,
            food_cost_percent=30,
            utilities=0,
            marketing=0,
            other_expenses=0,
            working_days=30,
        )
        self.assertEqual(result["fixed_costs"], 0.0)
        # With zero fixed costs, break-even daily customers = 0
        self.assertIsNotNone(result["break_even_customers_per_day"])
        self.assertAlmostEqual(result["break_even_customers_per_day"], 0.0, places=4)

    def test_18_negative_food_cost_percent_raises(self):
        """food_cost_percent < 0 must raise ValueError."""
        with self.assertRaises(ValueError):
            simulate_financials(
                customers_per_day=100,
                average_order_value=300,
                rent=100_000,
                staff_cost=150_000,
                food_cost_percent=-5,
                utilities=20_000,
                marketing=15_000,
                other_expenses=15_000,
            )

    def test_19_return_type_correctness(self):
        """Return values have the expected Python types."""
        result = self._run_reference()

        self.assertIsInstance(result["monthly_customers"], int)
        self.assertIsInstance(result["monthly_revenue"], float)
        self.assertIsInstance(result["food_cost"], float)
        self.assertIsInstance(result["fixed_costs"], float)
        self.assertIsInstance(result["monthly_expenses"], float)
        self.assertIsInstance(result["estimated_operating_profit"], float)
        self.assertIsInstance(result["operating_profit_margin"], float)
        # break_even_customers_per_day is float or None
        bep = result["break_even_customers_per_day"]
        self.assertTrue(isinstance(bep, float) or bep is None)

    def test_20_non_default_working_days(self):
        """Non-default working_days = 26 changes revenue and break-even correctly."""
        cpd, aov, days = 50, 250, 26
        rent, staff, utils, mktg, other = 40_000, 60_000, 8_000, 4_000, 3_000
        food_pct = 30

        result = simulate_financials(
            customers_per_day=cpd,
            average_order_value=aov,
            rent=rent,
            staff_cost=staff,
            food_cost_percent=food_pct,
            utilities=utils,
            marketing=mktg,
            other_expenses=other,
            working_days=days,
        )

        expected_revenue = cpd * days * aov
        self.assertEqual(result["monthly_customers"], cpd * days)
        self.assertAlmostEqual(result["monthly_revenue"], expected_revenue, places=2)

        # Break-even
        contribution = aov * (1 - food_pct / 100)
        fixed = rent + staff + utils + mktg + other
        expected_bep = (fixed / contribution) / days
        self.assertAlmostEqual(
            result["break_even_customers_per_day"],
            round(expected_bep, 4),
            places=4,
        )


if __name__ == "__main__":
    unittest.main()
