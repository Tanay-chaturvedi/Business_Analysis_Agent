"""
Automated Financial Engine Accuracy & Transparency Tests for BizAdvisor.
Covers the 11 core requirements:
1. Revenue calculation using known inputs.
2. Average spend derived from cost for two.
3. Fixed expenses adding up correctly without discrepancy.
4. Total operating expenses reconciling with itemized costs.
5. Operating profit and margin calculations.
6. Break-even customers per day and whole-customer target.
7. Zero revenue handling without division-by-zero crashes.
8. Zero and negative contribution margin handling.
9. Invalid and negative input rejection.
10. Editing assumptions and recalculating results.
11. Consistency between backend financial results and API endpoints.
"""

import os
import sys
import math
import pytest
from fastapi.testclient import TestClient

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import app
from src.finance.simulator import simulate_financials

client = TestClient(app)


# -----------------------------------------------------------------------------
# 1. Revenue calculation using known inputs
# -----------------------------------------------------------------------------
def test_1_revenue_calculation_known_inputs():
    """Monthly Revenue = Daily Customers × Operating Days × Average Spend."""
    cpd = 100.0
    days = 30.0
    aov = 775.0  # e.g., derived from Cost for Two = ₹1,550

    result = simulate_financials(
        customers_per_day=cpd,
        average_order_value=aov,
        rent=60000.0,
        staff_cost=50000.0,
        food_cost_percent=30.0,
        utilities=15000.0,
        marketing=10000.0,
        other_expenses=5000.0,
        working_days=days,
    )

    expected_customers = 3000
    expected_revenue = 3000 * 775.0  # 2,325,000.0

    assert result["monthly_customers"] == expected_customers
    assert result["monthly_revenue"] == expected_revenue


# -----------------------------------------------------------------------------
# 2. Average spend derived from cost for two
# -----------------------------------------------------------------------------
def test_2_average_spend_derived_from_cost_for_two():
    """Average spend per customer is calculated as approx_cost_for_two / 2."""
    cost_for_two = 1550.0
    derived_aov = cost_for_two / 2.0
    assert derived_aov == 775.0

    result = simulate_financials(
        customers_per_day=80.0,
        average_order_value=derived_aov,
        rent=50000.0,
        staff_cost=40000.0,
        food_cost_percent=28.0,
        utilities=12000.0,
        marketing=8000.0,
        other_expenses=4000.0,
        working_days=26.0,
    )

    assert result["monthly_customers"] == 80 * 26  # 2080
    assert result["monthly_revenue"] == round(2080 * 775.0, 2)  # 1,612,000.0


# -----------------------------------------------------------------------------
# 3. Fixed expenses adding up correctly (Fixing the ₹5,000 discrepancy)
# -----------------------------------------------------------------------------
def test_3_fixed_expenses_reconciliation():
    """
    Fixed Costs = Rent + Staff Costs + Utilities + Marketing + Other Fixed Costs.
    Verifies that Rent (60k) + Staff (50k) + Utilities (15k) + Marketing (10k) + Other (5k)
    equals exactly ₹1,40,000 without any omitted or unexplained difference.
    """
    rent = 60000.0
    staff = 50000.0
    utils = 15000.0
    mktg = 10000.0
    other = 5000.0

    result = simulate_financials(
        customers_per_day=100.0,
        average_order_value=400.0,
        rent=rent,
        staff_cost=staff,
        food_cost_percent=30.0,
        utilities=utils,
        marketing=mktg,
        other_expenses=other,
        working_days=30.0,
    )

    expected_fixed = rent + staff + utils + mktg + other  # 140,000.0
    assert result["fixed_costs"] == 140000.0
    assert result["rent"] == rent
    assert result["staff_cost"] == staff
    assert result["utilities"] == utils
    assert result["marketing"] == mktg
    assert result["other_expenses"] == other

    # Reconcile exact sum of itemized fields
    sum_itemized = (
        result["rent"]
        + result["staff_cost"]
        + result["utilities"]
        + result["marketing"]
        + result["other_expenses"]
    )
    assert sum_itemized == result["fixed_costs"]


# -----------------------------------------------------------------------------
# 4. Total operating expenses reconciling with itemized costs
# -----------------------------------------------------------------------------
def test_4_total_operating_expenses_reconciliation():
    """
    Total Operating Expenses = Fixed Costs + Variable Costs.
    Must always reconcile mathematically.
    """
    result = simulate_financials(
        customers_per_day=120.0,
        average_order_value=500.0,
        rent=75000.0,
        staff_cost=65000.0,
        food_cost_percent=32.0,
        utilities=18000.0,
        marketing=12000.0,
        other_expenses=6000.0,
        working_days=30.0,
    )

    revenue = 120.0 * 30.0 * 500.0  # 1,800,000.0
    variable_costs = revenue * 0.32  # 576,000.0
    fixed_costs = 75000.0 + 65000.0 + 18000.0 + 12000.0 + 6000.0  # 176,000.0
    expected_total_expenses = fixed_costs + variable_costs  # 752,000.0

    assert result["monthly_revenue"] == revenue
    assert result["variable_costs"] == variable_costs
    assert result["fixed_costs"] == fixed_costs
    assert result["monthly_expenses"] == expected_total_expenses
    assert result["monthly_expenses"] == result["fixed_costs"] + result["variable_costs"]


# -----------------------------------------------------------------------------
# 5. Operating profit and margin calculations
# -----------------------------------------------------------------------------
def test_5_operating_profit_and_margin_calculations():
    """
    Operating Profit = Monthly Revenue - Total Operating Expenses.
    Operating Margin (%) = Operating Profit / Monthly Revenue * 100.
    """
    # 1. Profitable case
    res_profit = simulate_financials(
        customers_per_day=100.0,
        average_order_value=775.0,
        rent=60000.0,
        staff_cost=50000.0,
        food_cost_percent=30.0,
        utilities=15000.0,
        marketing=10000.0,
        other_expenses=5000.0,
        working_days=30.0,
    )
    rev = 2325000.0
    exp = 140000.0 + (2325000.0 * 0.30)  # 140,000 + 697,500 = 837,500
    expected_profit = rev - exp  # 1,487,500.0
    expected_margin = (expected_profit / rev) * 100.0

    assert res_profit["estimated_operating_profit"] == expected_profit
    assert math.isclose(res_profit["operating_profit_margin"], round(expected_margin, 4), rel_tol=1e-4)

    # 2. Loss-making case
    res_loss = simulate_financials(
        customers_per_day=10.0,
        average_order_value=200.0,
        rent=100000.0,
        staff_cost=80000.0,
        food_cost_percent=40.0,
        utilities=20000.0,
        marketing=15000.0,
        other_expenses=10000.0,
        working_days=30.0,
    )
    assert res_loss["estimated_operating_profit"] < 0
    assert res_loss["operating_profit_margin"] < 0


# -----------------------------------------------------------------------------
# 6. Break-even customers per day & whole-customer target
# -----------------------------------------------------------------------------
def test_6_break_even_customers_and_target():
    """
    Contribution Margin Ratio = 1 - Variable Cost %
    Break-Even Revenue = Fixed Costs / Contribution Margin Ratio
    Break-Even Customers / Day = Fixed Costs / (AOV × Contribution Margin Ratio) / Working Days
    Whole-customer target = ceil(Break-Even Customers / Day)
    """
    res = simulate_financials(
        customers_per_day=100.0,
        average_order_value=775.0,
        rent=60000.0,
        staff_cost=50000.0,
        food_cost_percent=30.0,
        utilities=15000.0,
        marketing=10000.0,
        other_expenses=5000.0,
        working_days=30.0,
    )

    contrib_ratio = 1.0 - 0.30  # 0.70
    fixed = 140000.0
    expected_bep_revenue = fixed / contrib_ratio  # 200,000.0
    expected_bep_monthly = fixed / (775.0 * contrib_ratio)  # 258.064516...
    expected_bep_daily = expected_bep_monthly / 30.0  # 8.60215...
    expected_target = math.ceil(expected_bep_daily)  # 9

    assert math.isclose(res["contribution_margin_ratio"], 0.70, rel_tol=1e-4)
    assert math.isclose(res["break_even_revenue"], expected_bep_revenue, rel_tol=1e-2)
    assert math.isclose(res["break_even_customers_per_day"], round(expected_bep_daily, 4), rel_tol=1e-3)
    assert res["break_even_target_customers_per_day"] == expected_target
    assert res["break_even_achievable"] is True
    assert "9 customers required per day" in res["break_even_explanation"]


# -----------------------------------------------------------------------------
# 7. Zero revenue without division-by-zero crash
# -----------------------------------------------------------------------------
def test_7_zero_revenue_no_crash():
    """Zero customers or zero AOV produces 0.0 margin without division-by-zero error."""
    res_zero_cpd = simulate_financials(
        customers_per_day=0.0,
        average_order_value=500.0,
        rent=50000.0,
        staff_cost=40000.0,
        food_cost_percent=30.0,
        utilities=10000.0,
        marketing=5000.0,
        other_expenses=5000.0,
        working_days=30.0,
    )
    assert res_zero_cpd["monthly_revenue"] == 0.0
    assert res_zero_cpd["operating_profit_margin"] == 0.0
    assert res_zero_cpd["estimated_operating_profit"] == -110000.0

    res_zero_aov = simulate_financials(
        customers_per_day=100.0,
        average_order_value=0.0,
        rent=50000.0,
        staff_cost=40000.0,
        food_cost_percent=30.0,
        utilities=10000.0,
        marketing=5000.0,
        other_expenses=5000.0,
        working_days=30.0,
    )
    assert res_zero_aov["monthly_revenue"] == 0.0
    assert res_zero_aov["operating_profit_margin"] == 0.0
    assert res_zero_aov["break_even_achievable"] is False


# -----------------------------------------------------------------------------
# 8. Zero and negative contribution margin handling
# -----------------------------------------------------------------------------
def test_8_zero_and_negative_contribution_margin():
    """Variable cost >= 100% leaves no contribution margin; handled safely."""
    res_100 = simulate_financials(
        customers_per_day=50.0,
        average_order_value=300.0,
        rent=40000.0,
        staff_cost=30000.0,
        food_cost_percent=100.0,
        utilities=10000.0,
        marketing=5000.0,
        other_expenses=5000.0,
        working_days=30.0,
    )
    assert res_100["contribution_margin_ratio"] == 0.0
    assert res_100["break_even_achievable"] is False
    assert res_100["break_even_customers_per_day"] is None
    assert res_100["break_even_target_customers_per_day"] is None
    assert "Break-even cannot be achieved" in res_100["break_even_explanation"]

    # When all fixed costs are zero, 0 customers break even
    res_zero_fixed = simulate_financials(
        customers_per_day=50.0,
        average_order_value=300.0,
        rent=0.0,
        staff_cost=0.0,
        food_cost_percent=30.0,
        utilities=0.0,
        marketing=0.0,
        other_expenses=0.0,
        working_days=30.0,
    )
    assert res_zero_fixed["fixed_costs"] == 0.0
    assert res_zero_fixed["break_even_customers_per_day"] == 0.0
    assert res_zero_fixed["break_even_target_customers_per_day"] == 0
    assert res_zero_fixed["break_even_achievable"] is True


# -----------------------------------------------------------------------------
# 9. Invalid and negative input rejection
# -----------------------------------------------------------------------------
def test_9_invalid_and_negative_input_rejection():
    """Validates boundary conditions: non-negative amounts, 1-31 working days, 0-100% food cost."""
    # Negative customers
    with pytest.raises(ValueError) as exc:
        simulate_financials(-1, 400, 50000, 40000, 30, 10000, 5000, 5000, 30)
    assert "customers_per_day" in str(exc.value)

    # Negative rent
    with pytest.raises(ValueError) as exc:
        simulate_financials(100, 400, -50000, 40000, 30, 10000, 5000, 5000, 30)
    assert "rent" in str(exc.value)

    # Invalid working days (< 1 or > 31)
    with pytest.raises(ValueError) as exc:
        simulate_financials(100, 400, 50000, 40000, 30, 10000, 5000, 5000, 0)
    assert "working_days" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        simulate_financials(100, 400, 50000, 40000, 30, 10000, 5000, 5000, 32)
    assert "working_days" in str(exc.value)

    # Invalid food cost percent (> 100 or < 0)
    with pytest.raises(ValueError) as exc:
        simulate_financials(100, 400, 50000, 40000, 105, 10000, 5000, 5000, 30)
    assert "food_cost_percent" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        simulate_financials(100, 400, 50000, 40000, -5, 10000, 5000, 5000, 30)
    assert "food_cost_percent" in str(exc.value)


# -----------------------------------------------------------------------------
# 10. Editing assumptions and recalculating results
# -----------------------------------------------------------------------------
def test_10_editing_assumptions_and_recalculating():
    """Modifying assumptions changes projections deterministically."""
    base = simulate_financials(
        customers_per_day=100.0,
        average_order_value=400.0,
        rent=60000.0,
        staff_cost=50000.0,
        food_cost_percent=30.0,
        utilities=15000.0,
        marketing=10000.0,
        other_expenses=5000.0,
        working_days=30.0,
    )

    # Scenario: Higher volume (150 cust/day), negotiated lower rent (45,000)
    adjusted = simulate_financials(
        customers_per_day=150.0,
        average_order_value=400.0,
        rent=45000.0,
        staff_cost=50000.0,
        food_cost_percent=30.0,
        utilities=15000.0,
        marketing=10000.0,
        other_expenses=5000.0,
        working_days=30.0,
    )

    assert adjusted["monthly_revenue"] > base["monthly_revenue"]
    assert adjusted["fixed_costs"] < base["fixed_costs"]
    assert adjusted["estimated_operating_profit"] > base["estimated_operating_profit"]
    assert adjusted["break_even_customers_per_day"] < base["break_even_customers_per_day"]


# -----------------------------------------------------------------------------
# 11. Consistency between backend financial results and API endpoints
# -----------------------------------------------------------------------------
def test_11_backend_api_and_consistency():
    """POST /api/financial/simulate produces identical results to simulator function."""
    payload = {
        "customers_per_day": 100.0,
        "average_order_value": 775.0,
        "rent": 60000.0,
        "staff_cost": 50000.0,
        "food_cost_percent": 30.0,
        "utilities": 15000.0,
        "marketing": 10000.0,
        "other_expenses": 5000.0,
        "working_days": 30.0,
    }

    response = client.post("/api/financial/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    direct = simulate_financials(**payload)
    assert data["monthly_revenue"] == direct["monthly_revenue"]
    assert data["fixed_costs"] == direct["fixed_costs"]
    assert data["monthly_expenses"] == direct["monthly_expenses"]
    assert data["estimated_operating_profit"] == direct["estimated_operating_profit"]
    assert data["break_even_target_customers_per_day"] == direct["break_even_target_customers_per_day"]
    assert data["break_even_customers_per_day"] == direct["break_even_customers_per_day"]

    # Invalid input returns 422
    bad_resp = client.post("/api/financial/simulate", json={"working_days": 40})
    assert bad_resp.status_code == 422
