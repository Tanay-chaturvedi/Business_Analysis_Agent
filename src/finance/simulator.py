"""
Financial Simulator — Phase 3
==============================

A deterministic, assumption-based financial simulator for restaurant
and food-service businesses.

PURPOSE
-------
Helps a business owner produce a quick first-pass estimate of:

    - Monthly Revenue
    - Food / Variable Cost
    - Fixed Monthly Operating Costs
    - Total Monthly Operating Expenses
    - Estimated Operating Profit
    - Operating Profit Margin
    - Break-even Customers Per Day

This is NOT a machine-learning prediction.
Gemini / LLM is NOT used for any calculation here.

IMPORTANT LIMITATIONS
---------------------
The result is labelled "Estimated Operating Profit", NOT "Net Profit".

This simulator does NOT currently model:
    - Income tax or GST
    - Loan interest or EMI payments
    - Depreciation of equipment / furniture
    - Payment gateway charges
    - Delivery platform commissions (Zomato, Swiggy, etc.)
    - Inventory wastage / shrinkage
    - Maintenance and repair costs
    - Owner drawings or owner salary

All inputs are assumed to be in INR.
No currency symbol is embedded in the returned numbers.

Use this output only as a directional planning estimate.
"""

from __future__ import annotations
import math
from typing import Optional


def simulate_financials(
    customers_per_day: float,
    average_order_value: float,
    rent: float,
    staff_cost: float,
    food_cost_percent: float = 30.0,
    utilities: float = 15000.0,
    marketing: float = 10000.0,
    other_expenses: float = 5000.0,
    working_days: float = 30.0,
    variable_cost_percent: Optional[float] = None,
) -> dict:
    """
    Run the deterministic financial simulation and return a structured,
    fully-reconciled results dictionary.

    Parameters
    ----------
    customers_per_day : float
        Expected number of customers served per operating day. Must be >= 0.
    average_order_value : float
        Expected average spend per customer (INR). Must be >= 0.
    rent : float
        Monthly rent / lease cost (INR). Must be >= 0.
    staff_cost : float
        Total monthly staff salaries and wages (INR). Must be >= 0.
    food_cost_percent : float, optional
        Variable / food cost as a percentage of revenue (0–100). Default is 30.0.
    utilities : float, optional
        Monthly utilities — electricity, water, gas, internet (INR). Must be >= 0. Default is 15000.0.
    marketing : float, optional
        Monthly marketing and advertising spend (INR). Must be >= 0. Default is 10000.0.
    other_expenses : float, optional
        Other fixed monthly operating expenses (INR). Must be >= 0. Default is 5000.0.
    working_days : float, optional
        Number of operating days per month. Must be between 1 and 31. Default is 30.0.
    variable_cost_percent : float, optional
        Alias for food_cost_percent. If provided, overrides food_cost_percent.

    Returns
    -------
    dict
        Structured results dictionary with itemized and aggregate figures.

    Raises
    ------
    ValueError
        If any input fails validation.
    """
    if variable_cost_percent is not None:
        food_cost_percent = variable_cost_percent

    # ------------------------------------------------------------------
    # Normalise inputs to float
    # ------------------------------------------------------------------
    customers_per_day = float(customers_per_day)
    average_order_value = float(average_order_value)
    rent = float(rent)
    staff_cost = float(staff_cost)
    food_cost_percent = float(food_cost_percent)
    utilities = float(utilities)
    marketing = float(marketing)
    other_expenses = float(other_expenses)
    working_days = float(working_days)

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------
    if customers_per_day < 0:
        raise ValueError(
            f"customers_per_day must be >= 0, got {customers_per_day}."
        )
    if average_order_value < 0:
        raise ValueError(
            f"average_order_value must be >= 0, got {average_order_value}."
        )
    if rent < 0:
        raise ValueError(f"rent must be >= 0, got {rent}.")
    if staff_cost < 0:
        raise ValueError(f"staff_cost must be >= 0, got {staff_cost}.")
    if utilities < 0:
        raise ValueError(f"utilities must be >= 0, got {utilities}.")
    if marketing < 0:
        raise ValueError(f"marketing must be >= 0, got {marketing}.")
    if other_expenses < 0:
        raise ValueError(f"other_expenses must be >= 0, got {other_expenses}.")
    if not (0 <= food_cost_percent <= 100):
        raise ValueError(
            f"food_cost_percent must be between 0 and 100, got {food_cost_percent}."
        )
    if not (1 <= working_days <= 31):
        raise ValueError(
            f"working_days must be between 1 and 31, got {working_days}."
        )

    # ------------------------------------------------------------------
    # A) Monthly Customers
    # ------------------------------------------------------------------
    monthly_customers = customers_per_day * working_days

    # ------------------------------------------------------------------
    # B) Monthly Revenue
    #    Monthly Revenue = Daily Customers × Operating Days × Average Spend
    # ------------------------------------------------------------------
    monthly_revenue = monthly_customers * average_order_value

    # ------------------------------------------------------------------
    # C) Variable / Food Cost
    #    Variable Costs = Monthly Revenue × Variable Cost Percentage
    # ------------------------------------------------------------------
    variable_cost_ratio = food_cost_percent / 100.0
    food_cost = monthly_revenue * variable_cost_ratio

    # ------------------------------------------------------------------
    # D) Fixed Monthly Operating Costs
    #    Fixed Costs = Rent + Staff Costs + Utilities + Marketing + Other Fixed Costs
    # ------------------------------------------------------------------
    fixed_costs = rent + staff_cost + utilities + marketing + other_expenses

    # ------------------------------------------------------------------
    # E) Total Monthly Operating Expenses
    #    Total Operating Expenses = Variable Costs + Fixed Costs
    # ------------------------------------------------------------------
    monthly_expenses = fixed_costs + food_cost

    # ------------------------------------------------------------------
    # F) Estimated Operating Profit
    #    Operating Profit = Monthly Revenue − Total Operating Expenses
    # ------------------------------------------------------------------
    estimated_operating_profit = monthly_revenue - monthly_expenses

    # ------------------------------------------------------------------
    # G) Operating Profit Margin
    #    Operating Margin (%) = Operating Profit / Monthly Revenue × 100
    #    Safely handles zero revenue (returns 0.0)
    # ------------------------------------------------------------------
    if monthly_revenue > 0:
        operating_profit_margin = (estimated_operating_profit / monthly_revenue) * 100.0
    else:
        operating_profit_margin = 0.0

    # ------------------------------------------------------------------
    # H) Contribution Margin & Break-even Calculations
    #    Contribution Margin Ratio = 1 − Variable Cost Percentage
    #    Break-Even Revenue = Fixed Operating Costs / Contribution Margin Ratio
    #    Break-Even Customers per Month = Fixed Operating Costs / (Avg Spend × Contribution Margin Ratio)
    #    Break-Even Customers per Day = Break-Even Customers per Month / Operating Days
    # ------------------------------------------------------------------
    contribution_margin_ratio = 1.0 - variable_cost_ratio

    if contribution_margin_ratio <= 0.0:
        # Variable cost equals or exceeds 100% of revenue — break-even is mathematically impossible
        break_even_revenue: Optional[float] = None
        break_even_customers_monthly: Optional[float] = None
        break_even_customers_per_day: Optional[float] = None
        break_even_target_customers_per_day: Optional[int] = None
        break_even_achievable = False
        break_even_explanation = (
            "Break-even cannot be achieved under the current assumptions because variable costs "
            "equal or exceed 100% of revenue, leaving no contribution margin to cover fixed operating costs."
        )
    elif fixed_costs == 0.0:
        break_even_revenue = 0.0
        break_even_customers_monthly = 0.0
        break_even_customers_per_day = 0.0
        break_even_target_customers_per_day = 0
        break_even_achievable = True
        break_even_explanation = (
            "Fixed operating costs are ₹0; break-even is achieved with 0 customers."
        )
    else:
        break_even_revenue = fixed_costs / contribution_margin_ratio

        if average_order_value <= 0.0:
            break_even_customers_monthly = None
            break_even_customers_per_day = None
            break_even_target_customers_per_day = None
            break_even_achievable = False
            break_even_explanation = (
                "Break-even cannot be achieved because average spend per customer is ₹0 while fixed operating costs exist."
            )
        else:
            break_even_customers_monthly = fixed_costs / (average_order_value * contribution_margin_ratio)
            break_even_customers_per_day = break_even_customers_monthly / working_days
            break_even_target_customers_per_day = int(math.ceil(break_even_customers_per_day))
            break_even_achievable = True
            break_even_explanation = (
                f"Estimated {break_even_target_customers_per_day} customers required per day "
                f"({round(break_even_customers_per_day, 1)} exact) to cover all fixed and variable operating costs."
            )

    # ------------------------------------------------------------------
    # Canonical Output Mapping
    # All monetary numbers rounded to 2 decimals; margins/break-even to 4 decimals
    # ------------------------------------------------------------------
    return {
        "monthly_customers": int(round(monthly_customers)),
        "monthly_revenue": round(monthly_revenue, 2),
        "variable_costs": round(food_cost, 2),
        "food_cost": round(food_cost, 2),  # Preserved for backward compatibility
        "rent": round(rent, 2),
        "staff_cost": round(staff_cost, 2),
        "utilities": round(utilities, 2),
        "marketing": round(marketing, 2),
        "other_expenses": round(other_expenses, 2),
        "fixed_costs": round(fixed_costs, 2),
        "monthly_expenses": round(monthly_expenses, 2),
        "estimated_operating_profit": round(estimated_operating_profit, 2),
        "operating_profit_margin": round(operating_profit_margin, 4),
        "contribution_margin_ratio": round(contribution_margin_ratio, 4),
        "break_even_revenue": round(break_even_revenue, 2) if break_even_revenue is not None else None,
        "break_even_customers_per_month": (
            round(break_even_customers_monthly, 4)
            if break_even_customers_monthly is not None
            else None
        ),
        "break_even_customers_per_day": (
            round(break_even_customers_per_day, 4)
            if break_even_customers_per_day is not None
            else None
        ),
        "break_even_target_customers_per_day": break_even_target_customers_per_day,
        "break_even_achievable": break_even_achievable,
        "break_even_explanation": break_even_explanation,
        "assumptions": {
            "customers_per_day": round(customers_per_day, 2),
            "working_days": round(working_days, 2),
            "average_order_value": round(average_order_value, 2),
            "rent": round(rent, 2),
            "staff_cost": round(staff_cost, 2),
            "utilities": round(utilities, 2),
            "marketing": round(marketing, 2),
            "other_expenses": round(other_expenses, 2),
            "food_cost_percent": round(food_cost_percent, 2),
            "variable_cost_percent": round(food_cost_percent, 2),
        },
    }
