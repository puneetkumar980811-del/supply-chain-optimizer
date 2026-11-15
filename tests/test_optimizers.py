"""
Unit Tests for Supply Chain Optimization Models.
Verifies mathematical formulations, constraints, and edge cases.
"""

import pytest
import numpy as np
import pandas as pd

from models.transportation_lp import solve_transportation_problem
from models.facility_location import solve_facility_location
from models.inventory_eoq import calculate_eoq, calculate_safety_stock_rop, generate_eoq_cost_curve
from models.vrp_router import solve_cvrp, calculate_distance_matrix, two_opt_optimize
from models.demand_forecaster import run_comprehensive_forecast, calculate_forecast_metrics


def test_transportation_problem_balanced():
    """Test standard balanced transportation linear program."""
    supply = {"Plant_A": 100, "Plant_B": 150}
    demand = {"Market_1": 80, "Market_2": 170}
    costs = {
        "Plant_A": {"Market_1": 4.0, "Market_2": 8.0},
        "Plant_B": {"Market_1": 5.0, "Market_2": 6.0},
    }

    res = solve_transportation_problem(supply, demand, costs)
    assert res["status"] == "Optimal"
    assert res["is_optimal"] is True
    assert res["is_balanced"] is True
    # In optimal allocation: Plant_A -> Market_1 (80), Plant_A -> Market_2 (20), Plant_B -> Market_2 (150)
    # Total cost = 80*4 + 20*8 + 150*6 = 320 + 160 + 900 = 1380
    assert abs(res["total_cost"] - 1380.0) < 1e-2


def test_transportation_problem_excess_supply():
    """Test unbalanced transportation problem where supply exceeds demand."""
    supply = {"Plant_A": 200, "Plant_B": 200}
    demand = {"Market_1": 100, "Market_2": 150}
    costs = {
        "Plant_A": {"Market_1": 2.0, "Market_2": 7.0},
        "Plant_B": {"Market_1": 5.0, "Market_2": 3.0},
    }

    res = solve_transportation_problem(supply, demand, costs)
    assert res["status"] == "Optimal"
    assert res["total_demand"] == 250
    # Plant A satisfies Market 1 (100*2 = 200), Plant B satisfies Market 2 (150*3 = 450) -> 650
    assert abs(res["total_cost"] - 650.0) < 1e-2


def test_facility_location_milp():
    """Test Capacitated Facility Location MILP solver."""
    warehouses = [
        {"id": "W1", "name": "North DC", "capacity": 500, "fixed_cost": 5000},
        {"id": "W2", "name": "South DC", "capacity": 500, "fixed_cost": 12000},
    ]
    customers = [
        {"id": "C1", "name": "City 1", "demand": 300},
        {"id": "C2", "name": "City 2", "demand": 150},
    ]
    # Total demand = 450. W1 alone has capacity 500 and lower fixed cost (5000).
    # If shipping costs are comparable, W1 should be opened and W2 closed.
    costs = {
        "W1": {"C1": 10.0, "C2": 12.0},
        "W2": {"C1": 11.0, "C2": 13.0},
    }

    res = solve_facility_location(warehouses, customers, costs)
    assert res["status"] == "Optimal"
    assert res["open_facilities_count"] == 1
    assert res["open_facilities"][0]["id"] == "W1"
    assert len(res["closed_facilities"]) == 1
    assert res["closed_facilities"][0]["id"] == "W2"


def test_eoq_optimality_condition():
    """At optimal EOQ, annual holding cost must equal annual ordering cost."""
    D = 12000.0  # Annual demand
    S = 250.0    # Ordering cost
    C = 50.0     # Unit cost
    h = 0.20     # Holding cost 20% -> H = 10.0

    # EOQ = sqrt(2 * 12000 * 250 / 10) = sqrt(600,000) = 774.596...
    res = calculate_eoq(D, S, C, h)
    assert abs(res["eoq"] - 774.6) < 1.0

    # Holding cost and ordering cost should be almost identical
    diff = abs(res["annual_holding_cost"] - res["annual_ordering_cost"])
    assert diff < 5.0  # slight rounding on EOQ units


def test_safety_stock_monotonicity():
    """Safety stock must strictly increase with higher service levels."""
    annual_demand = 36500.0  # 100 units/day
    lead_time = 7.0          # 7 days

    ss_90 = calculate_safety_stock_rop(annual_demand, lead_time, service_level=0.90)
    ss_95 = calculate_safety_stock_rop(annual_demand, lead_time, service_level=0.95)
    ss_99 = calculate_safety_stock_rop(annual_demand, lead_time, service_level=0.99)

    assert ss_90["safety_stock"] < ss_95["safety_stock"] < ss_99["safety_stock"]
    assert ss_90["reorder_point"] < ss_95["reorder_point"] < ss_99["reorder_point"]


def test_cvrp_solver():
    """Test Capacitated Vehicle Routing Problem logic."""
    depot = {"id": "D0", "name": "Depot", "lat": 19.0, "lon": 73.0}
    customers = [
        {"id": "C1", "name": "Stop 1", "lat": 19.1, "lon": 73.1, "demand": 40},
        {"id": "C2", "name": "Stop 2", "lat": 19.2, "lon": 73.2, "demand": 50},
        {"id": "C3", "name": "Stop 3", "lat": 19.3, "lon": 73.3, "demand": 60},
    ]

    # Vehicle capacity = 100 -> requires at least 2 vehicles for total demand 150
    res = solve_cvrp(depot, customers, vehicle_capacity=100)
    assert res["vehicles_used"] >= 2
    assert res["total_distance_km"] > 0
    # Every vehicle route must start and end at depot (index 0)
    for r in res["vehicle_routes"]:
        assert r["route_indices"][0] == 0
        assert r["route_indices"][-1] == 0


def test_demand_forecasting_pipeline():
    """Test forecasting algorithms on sample time-series."""
    df = pd.DataFrame({
        "Month": [f"2025-{i:02d}" for i in range(1, 13)],
        "Demand": [100, 110, 120, 115, 130, 140, 150, 155, 165, 175, 185, 195],
    })

    res = run_comprehensive_forecast(df, demand_col="Demand", time_col="Month", forecast_periods=3)
    assert res["projected_demand"] > 0
    assert not res["metrics_df"].empty
    assert len(res["result_df"]) == 15  # 12 historical + 3 forecast
