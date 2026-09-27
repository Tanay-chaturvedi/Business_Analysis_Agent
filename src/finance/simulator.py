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


def simulate_financials(
    customers_per_day: float,
    average_order_value: float,
    rent: float,
    staff_cost: float,
    food_cost_percent: float,
    utilities: float,
    marketing: float,
    other_expenses: float,
    working_days: float = 30,
) -> dict:
    """
    Run the financial simulation and return a structured results dictionary.

    Parameters
    ----------
    customers_per_day : float
        Expected number of customers served per working day. Must be >= 0.
    average_order_value : float
        Expected average spend per customer (INR). Must be >= 0.
    rent : float
        Monthly rent / lease cost (INR). Must be >= 0.
    staff_cost : float
        Total monthly staff salaries and wages (INR). Must be >= 0.
    food_cost_percent : float
        Food / variable cost as a percentage of revenue (0–100).
    utilities : float
        Monthly utilities — electricity, water, gas, internet (INR). Must be >= 0.
    marketing : float
        Monthly marketing and advertising spend (INR). Must be >= 0.
    other_expenses : float
        Any other monthly operating expenses not listed above (INR). Must be >= 0.
    working_days : float, optional
        Number of operating days per month. Must be > 0. Default is 30.

    Returns
    -------
    dict
        {
            "monthly_customers"            : int,
            "monthly_revenue"              : float,
            "food_cost"                    : float,
            "fixed_costs"                  : float,
            "monthly_expenses"             : float,
            "estimated_operating_profit"   : float,
            "operating_profit_margin"      : float,   # percentage
            "break_even_customers_per_day" : float | None
        }

    Raises
    ------
    ValueError
        If any input fails validation (see 'Input Validation' section below).

    Notes
    -----
    All monetary values returned are in INR.
    Percentages are returned as plain numbers (e.g. 25.0 means 25%).
    break_even_customers_per_day is None when contribution_per_customer == 0.
    """

    # ------------------------------------------------------------------
    # Normalise inputs to float so all arithmetic and returned values
    # are consistently float regardless of the caller's numeric type.
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
    if working_days <= 0:
        raise ValueError(
            f"working_days must be > 0, got {working_days}."
        )

    # ------------------------------------------------------------------
    # A) Monthly Customers
    # ------------------------------------------------------------------
    monthly_customers = customers_per_day * working_days

    # ------------------------------------------------------------------
    # B) Monthly Revenue
    # ------------------------------------------------------------------
    monthly_revenue = monthly_customers * average_order_value

    # ------------------------------------------------------------------
    # C) Food / Variable Cost
    # ------------------------------------------------------------------
    food_cost = monthly_revenue * (food_cost_percent / 100)

    # ------------------------------------------------------------------
    # D) Fixed Monthly Operating Costs
    # ------------------------------------------------------------------
    fixed_costs = rent + staff_cost + utilities + marketing + other_expenses

    # ------------------------------------------------------------------
    # E) Total Monthly Operating Expenses
    # ------------------------------------------------------------------
    monthly_expenses = fixed_costs + food_cost

    # ------------------------------------------------------------------
    # F) Estimated Operating Profit
    # ------------------------------------------------------------------
    estimated_operating_profit = monthly_revenue - monthly_expenses

    # ------------------------------------------------------------------
    # G) Operating Profit Margin
    # ------------------------------------------------------------------
    if monthly_revenue > 0:
        operating_profit_margin = (estimated_operating_profit / monthly_revenue) * 100
    else:
        operating_profit_margin = 0.0

    # ------------------------------------------------------------------
    # H) Contribution Per Customer
    #    Revenue retained per customer after covering the variable
    #    (food) cost — available to cover fixed costs and profit.
    # ------------------------------------------------------------------
    contribution_per_customer = average_order_value * (1 - food_cost_percent / 100)

    # ------------------------------------------------------------------
    # I & J) Break-even Customers Per Day
    #    The number of customers needed per day so that total revenue
    #    exactly covers all fixed costs (after variable costs).
    #    Returns None when contribution_per_customer == 0 (would require
    #    infinite customers to cover any fixed cost).
    # ------------------------------------------------------------------
    if contribution_per_customer > 0:
        break_even_customers_monthly = fixed_costs / contribution_per_customer
        break_even_customers_per_day: float | None = (
            break_even_customers_monthly / working_days
        )
    else:
        break_even_customers_per_day = None

    # ------------------------------------------------------------------
    # Return — round for presentation; intermediate values were kept full
    # ------------------------------------------------------------------
    return {
        "monthly_customers": int(monthly_customers),
        "monthly_revenue": round(monthly_revenue, 2),
        "food_cost": round(food_cost, 2),
        "fixed_costs": round(fixed_costs, 2),
        "monthly_expenses": round(monthly_expenses, 2),
        "estimated_operating_profit": round(estimated_operating_profit, 2),
        "operating_profit_margin": round(operating_profit_margin, 4),
        "break_even_customers_per_day": (
            round(break_even_customers_per_day, 4)
            if break_even_customers_per_day is not None
            else None
        ),
    }
