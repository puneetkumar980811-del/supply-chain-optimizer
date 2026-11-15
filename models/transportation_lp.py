"""
Multi-Source to Multi-Destination Transportation Problem Solver.
Mathematical Formulation:
    Minimize Z = SUM(i) SUM(j) [ c_ij * x_ij + lambda * e_ij * x_ij ]
    Subject to:
        SUM(j) x_ij <= Supply_i       for all i in Supply Hubs
        SUM(i) x_ij >= Demand_j       for all j in Demand Centers
        x_ij >= 0                      for all i, j

Where:
    c_ij = Freight cost per unit shipped from node i to j
    e_ij = CO2 emission penalty factor per unit shipped
    lambda = Green supply chain emission weighting factor
    x_ij = Quantity transported from i to j
"""

import pulp
import pandas as pd
import numpy as np


def solve_transportation_problem(
    supply_dict,
    demand_dict,
    cost_matrix,
    distance_matrix=None,
    co2_per_ton_km=0.082,
    emission_weight=0.0,
    allow_unmet_demand=True,
    unmet_penalty=10000.0,
):
    """
    Solves the classic or green transportation linear program using PuLP CBC solver.

    Parameters:
    -----------
    supply_dict : dict
        {supply_node_id: available_capacity}
    demand_dict : dict
        {demand_node_id: required_quantity}
    cost_matrix : dict of dict
        {supply_node_id: {demand_node_id: unit_transport_cost}}
    distance_matrix : dict of dict, optional
        {supply_node_id: {demand_node_id: distance_km}}
    co2_per_ton_km : float
        Carbon emission factor (default: 0.082 kg CO2 / ton-km)
    emission_weight : float
        Trade-off weight between financial cost (₹) and carbon penalty (₹/kg CO2)
    allow_unmet_demand : bool
        If True, adds dummy penalty variables to prevent infeasibility when demand > supply

    Returns:
    --------
    dict containing:
        - status: str (Optimal, Infeasible, etc.)
        - total_cost: float
        - total_emissions_kg: float
        - flows: list of dicts [{'from': i, 'to': j, 'flow': qty, 'unit_cost': c, 'total_cost': val}]
        - flow_df: pd.DataFrame
        - supply_summary: pd.DataFrame
        - demand_summary: pd.DataFrame
        - is_balanced: bool
        - total_supply: float
        - total_demand: float
    """
    total_supply = sum(supply_dict.values())
    total_demand = sum(demand_dict.values())
    is_balanced = abs(total_supply - total_demand) < 1e-5

    # Initialize Linear Programming Problem
    model = pulp.LpProblem("OptiChain_Transportation_Problem", pulp.LpMinimize)

    supply_nodes = list(supply_dict.keys())
    demand_nodes = list(demand_dict.keys())

    # Decision variables: x_ij = flow from supply i to demand j
    x = pulp.LpVariable.dicts(
        "flow",
        [(i, j) for i in supply_nodes for j in demand_nodes],
        lowBound=0,
        cat=pulp.LpContinuous,
    )

    # Slack variable for unmet demand if supply is insufficient
    unmet = {}
    if allow_unmet_demand:
        unmet = pulp.LpVariable.dicts(
            "unmet",
            demand_nodes,
            lowBound=0,
            cat=pulp.LpContinuous,
        )

    # Objective function components:
    # 1. Transport freight cost
    freight_costs = []
    # 2. Environmental emissions penalty
    emission_penalties = []

    for i in supply_nodes:
        for j in demand_nodes:
            c = cost_matrix[i][j]
            freight_costs.append(c * x[(i, j)])

            if distance_matrix and emission_weight > 0:
                dist = distance_matrix.get(i, {}).get(j, 0.0)
                emissions_per_ton = dist * co2_per_ton_km
                emission_penalties.append(emission_weight * emissions_per_ton * x[(i, j)])

    objective = pulp.lpSum(freight_costs) + pulp.lpSum(emission_penalties)

    if allow_unmet_demand:
        penalty_terms = [unmet_penalty * unmet[j] for j in demand_nodes]
        objective += pulp.lpSum(penalty_terms)

    model += objective, "Total_Logistics_Cost"

    # Supply Constraints: SUM(j) x_ij <= Supply_i
    for i in supply_nodes:
        model += (
            pulp.lpSum([x[(i, j)] for j in demand_nodes]) <= supply_dict[i],
            f"Supply_Constraint_{i}",
        )

    # Demand Constraints: SUM(i) x_ij + unmet_j >= Demand_j
    for j in demand_nodes:
        if allow_unmet_demand:
            model += (
                pulp.lpSum([x[(i, j)] for i in supply_nodes]) + unmet[j] >= demand_dict[j],
                f"Demand_Constraint_{j}",
            )
        else:
            model += (
                pulp.lpSum([x[(i, j)] for i in supply_nodes]) >= demand_dict[j],
                f"Demand_Constraint_{j}",
            )

    # Solve with CBC solver silently
    solver = pulp.PULP_CBC_CMD(msg=False)
    status_code = model.solve(solver)
    status = pulp.LpStatus[status_code]

    # Process and format results
    flows = []
    total_pure_cost = 0.0
    total_emissions = 0.0

    if status == "Optimal":
        for i in supply_nodes:
            for j in demand_nodes:
                val = pulp.value(x[(i, j)])
                if val is not None and val > 1e-4:
                    val = round(float(val), 2)
                    c = cost_matrix[i][j]
                    dist = distance_matrix.get(i, {}).get(j, 0.0) if distance_matrix else 0.0
                    cost_val = round(val * c, 2)
                    emiss_val = round(val * dist * co2_per_ton_km, 2)
                    total_pure_cost += cost_val
                    total_emissions += emiss_val

                    flows.append({
                        "From": i,
                        "To": j,
                        "Flow_Units": val,
                        "Unit_Cost": c,
                        "Distance_km": dist,
                        "Total_Freight_Cost": cost_val,
                        "Emissions_kg_CO2": emiss_val,
                    })

    flow_df = pd.DataFrame(flows)

    # Node summaries
    supply_rows = []
    for i in supply_nodes:
        shipped = sum(
            pulp.value(x[(i, j)]) or 0.0
            for j in demand_nodes
            if pulp.value(x[(i, j)]) is not None
        )
        cap = supply_dict[i]
        supply_rows.append({
            "Supply_Hub": i,
            "Capacity": cap,
            "Utilized": round(shipped, 2),
            "Slack_Capacity": round(max(0.0, cap - shipped), 2),
            "Utilization_Pct": round((shipped / cap * 100.0) if cap > 0 else 0.0, 1),
        })
    supply_df = pd.DataFrame(supply_rows)

    demand_rows = []
    for j in demand_nodes:
        received = sum(
            pulp.value(x[(i, j)]) or 0.0
            for i in supply_nodes
            if pulp.value(x[(i, j)]) is not None
        )
        req = demand_dict[j]
        unmet_qty = round(pulp.value(unmet[j]) or 0.0, 2) if allow_unmet_demand else round(max(0.0, req - received), 2)
        demand_rows.append({
            "Demand_Center": j,
            "Requirement": req,
            "Fulfilled": round(received, 2),
            "Unmet": unmet_qty,
            "Fulfillment_Pct": round((received / req * 100.0) if req > 0 else 100.0, 1),
        })
    demand_df = pd.DataFrame(demand_rows)

    return {
        "status": status,
        "is_optimal": (status == "Optimal"),
        "total_cost": round(total_pure_cost, 2),
        "total_emissions_kg": round(total_emissions, 2),
        "total_objective_val": round(float(pulp.value(model.objective) or 0.0), 2),
        "flows": flows,
        "flow_df": flow_df,
        "supply_summary": supply_df,
        "demand_summary": demand_df,
        "is_balanced": is_balanced,
        "total_supply": total_supply,
        "total_demand": total_demand,
    }
