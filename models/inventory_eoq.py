"""
Inventory Optimization & Safety Stock Analytics (EOQ & ROP).
Mathematical Models:
    1. Economic Order Quantity (EOQ):
       Q* = sqrt((2 * D * S) / H)
       where:
         D = Annual Demand (units/year)
         S = Setup/Ordering Cost per order (₹)
         H = Annual Holding/Carrying Cost per unit (₹/unit/year)

    2. Total Inventory Cost:
       Total_Cost(Q) = (D / Q) * S + (Q / 2) * H + (D * C)
       where C = Unit purchase price

    3. Safety Stock & Reorder Point (Stochastic Demand):
       Safety_Stock (SS) = Z * sigma_L
       sigma_L = sqrt(L * sigma_d^2 + d^2 * sigma_L_days^2)
       ROP = (d * L) + SS
       where:
         d = Average daily demand
         L = Average supplier lead time (days)
         Z = Normal distribution inverse CDF factor for target service level (e.g. 1.645 for 95%)
"""

import numpy as np
import pandas as pd
from scipy.stats import norm


def calculate_eoq(annual_demand, ordering_cost, unit_cost, holding_cost_pct):
    """
    Computes Economic Order Quantity and cost breakdown.

    Parameters:
    -----------
    annual_demand : float
        Annual demand in units (D)
    ordering_cost : float
        Fixed cost per order placed (S)
    unit_cost : float
        Purchase price per unit (C)
    holding_cost_pct : float
        Annual holding cost as a percentage of unit cost (e.g., 20% = 0.20)

    Returns:
    --------
    dict of inventory metrics
    """
    annual_demand = max(1.0, float(annual_demand))
    ordering_cost = max(0.01, float(ordering_cost))
    unit_cost = max(0.01, float(unit_cost))
    holding_cost_pct = max(0.01, float(holding_cost_pct))

    h_cost_unit = unit_cost * (holding_cost_pct / 100.0 if holding_cost_pct > 1.0 else holding_cost_pct)

    # EOQ formula
    eoq = np.sqrt((2.0 * annual_demand * ordering_cost) / h_cost_unit)
    eoq = round(float(eoq), 1)

    # Orders per year and cycle time
    orders_per_year = round(annual_demand / eoq, 2)
    cycle_time_days = round(365.0 / orders_per_year, 1) if orders_per_year > 0 else 365.0

    # Annual costs at EOQ
    annual_ordering_cost = round((annual_demand / eoq) * ordering_cost, 2)
    annual_holding_cost = round((eoq / 2.0) * h_cost_unit, 2)
    annual_purchase_cost = round(annual_demand * unit_cost, 2)
    total_inventory_cost = round(annual_ordering_cost + annual_holding_cost, 2)
    grand_total_cost = round(total_inventory_cost + annual_purchase_cost, 2)

    return {
        "eoq": eoq,
        "holding_cost_per_unit_year": round(h_cost_unit, 2),
        "orders_per_year": orders_per_year,
        "cycle_time_days": cycle_time_days,
        "annual_ordering_cost": annual_ordering_cost,
        "annual_holding_cost": annual_holding_cost,
        "total_relevant_cost": total_inventory_cost,
        "grand_total_cost": grand_total_cost,
    }


def calculate_safety_stock_rop(
    annual_demand,
    lead_time_days,
    daily_demand_std=None,
    lead_time_std=0.0,
    service_level=0.95,
    working_days_per_year=365,
):
    """
    Computes Safety Stock and Reorder Point under stochastic demand & lead time.

    Parameters:
    -----------
    annual_demand : float
    lead_time_days : float (average lead time in days)
    daily_demand_std : float (standard deviation of daily demand)
    lead_time_std : float (standard deviation of lead time in days)
    service_level : float (e.g. 0.90, 0.95, 0.98, 0.99)
    working_days_per_year : int (default: 365)
    """
    avg_daily_demand = annual_demand / working_days_per_year

    if daily_demand_std is None or daily_demand_std <= 0:
        # Default estimation: 20% coefficient of variation
        daily_demand_std = 0.20 * avg_daily_demand

    # Z-score corresponding to target cycle service level
    z_score = float(norm.ppf(service_level))

    # Variance during lead time considering both demand and lead time variability
    # Var(DL) = L * sigma_d^2 + d^2 * sigma_L^2
    var_dl = (lead_time_days * (daily_demand_std ** 2)) + ((avg_daily_demand ** 2) * (lead_time_std ** 2))
    sigma_dl = np.sqrt(max(0.001, var_dl))

    safety_stock = round(float(z_score * sigma_dl), 1)
    lead_time_demand = round(float(avg_daily_demand * lead_time_days), 1)
    reorder_point = round(float(lead_time_demand + safety_stock), 1)

    return {
        "service_level_pct": round(service_level * 100.0, 1),
        "z_score": round(z_score, 3),
        "avg_daily_demand": round(avg_daily_demand, 2),
        "lead_time_demand": lead_time_demand,
        "sigma_lead_time_demand": round(float(sigma_dl), 2),
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
    }


def generate_eoq_cost_curve(annual_demand, ordering_cost, unit_cost, holding_cost_pct):
    """
    Generates data points for Plotly visualization of the U-shaped Total Cost Curve.
    Shows the intersection where Holding Cost equals Ordering Cost (Optimal EOQ).
    """
    res = calculate_eoq(annual_demand, ordering_cost, unit_cost, holding_cost_pct)
    optimal_q = res["eoq"]
    h_unit = res["holding_cost_per_unit_year"]

    # Sample order quantities from 20% of EOQ to 250% of EOQ
    q_min = max(5, int(optimal_q * 0.25))
    q_max = int(optimal_q * 2.5)
    q_values = np.linspace(q_min, q_max, 80)

    ordering_costs = (annual_demand / q_values) * ordering_cost
    holding_costs = (q_values / 2.0) * h_unit
    total_costs = ordering_costs + holding_costs

    df = pd.DataFrame({
        "Order_Quantity": np.round(q_values, 1),
        "Annual_Ordering_Cost": np.round(ordering_costs, 2),
        "Annual_Holding_Cost": np.round(holding_costs, 2),
        "Total_Relevant_Cost": np.round(total_costs, 2),
    })

    return df, res
