"""
Capacitated Facility Location & Warehouse Selection Solver (MILP).
Mathematical Formulation:
    Minimize Z = SUM(w) [ F_w * y_w ] + SUM(w) SUM(c) [ c_wc * x_wc ]
    Subject to:
        SUM(w) x_wc >= Demand_c                  for all c in Customers
        SUM(c) x_wc <= Capacity_w * y_w          for all w in Candidate Warehouses
        SUM(w) y_w <= max_facilities_to_open     (optional constraint)
        y_w in {0, 1}                            (binary decision: open or close)
        x_wc >= 0                                (continuous flow)

Where:
    F_w = Fixed operational cost to open warehouse w
    c_wc = Transportation cost per unit from warehouse w to customer c
    y_w = 1 if warehouse w is opened, 0 otherwise
    x_wc = Quantity shipped from warehouse w to customer c
"""

import pulp
import pandas as pd
import numpy as np


def solve_facility_location(
    candidate_warehouses,
    customers,
    cost_matrix,
    max_open_limit=None,
    force_open_ids=None,
    force_closed_ids=None,
):
    """
    Solves the Capacitated Facility Location Problem using Mixed-Integer Linear Programming.

    Parameters:
    -----------
    candidate_warehouses : list of dict
        [{'id': 'W1', 'name': 'Pune', 'capacity': 1100, 'fixed_cost': 180000}, ...]
    customers : list of dict
        [{'id': 'C1', 'name': 'Hyderabad', 'demand': 550}, ...]
    cost_matrix : dict of dict
        {warehouse_id: {customer_id: unit_shipping_cost}}
    max_open_limit : int, optional
        Maximum number of facilities allowed to open (p-facility constraint)
    force_open_ids : list of str, optional
        IDs of warehouses that MUST be opened
    force_closed_ids : list of str, optional
        IDs of warehouses that MUST be closed (e.g. maintenance/strike simulation)

    Returns:
    --------
    dict containing:
        - status: str
        - total_cost: float (fixed + shipping)
        - fixed_cost: float
        - variable_shipping_cost: float
        - open_facilities: list of dicts
        - closed_facilities: list of dicts
        - flow_df: pd.DataFrame
        - facility_summary_df: pd.DataFrame
        - customer_summary_df: pd.DataFrame
    """
    force_open_ids = force_open_ids or []
    force_closed_ids = force_closed_ids or []

    model = pulp.LpProblem("OptiChain_Facility_Location", pulp.LpMinimize)

    warehouse_ids = [w["id"] for w in candidate_warehouses]
    customer_ids = [c["id"] for c in customers]

    wh_dict = {w["id"]: w for w in candidate_warehouses}
    cust_dict = {c["id"]: c for c in customers}

    # Binary decision variable: y_w = 1 if warehouse w is open, 0 otherwise
    y = pulp.LpVariable.dicts("Open_Facility", warehouse_ids, cat=pulp.LpBinary)

    # Continuous decision variable: x_wc = quantity shipped from warehouse w to customer c
    x = pulp.LpVariable.dicts(
        "Shipment_Flow",
        [(w, c) for w in warehouse_ids for c in customer_ids],
        lowBound=0,
        cat=pulp.LpContinuous,
    )

    # Objective Function: Total Cost = Fixed Operating Cost + Variable Transportation Cost
    fixed_cost_terms = [wh_dict[w]["fixed_cost"] * y[w] for w in warehouse_ids]
    shipping_cost_terms = [
        cost_matrix[w][c] * x[(w, c)]
        for w in warehouse_ids
        for c in customer_ids
    ]

    model += pulp.lpSum(fixed_cost_terms) + pulp.lpSum(shipping_cost_terms), "Total_Network_Cost"

    # Constraint 1: Satisfy customer demand
    for c in customer_ids:
        model += (
            pulp.lpSum([x[(w, c)] for w in warehouse_ids]) >= cust_dict[c]["demand"],
            f"Demand_Requirement_{c}",
        )

    # Constraint 2: Warehouse capacity and linking constraint
    # SUM_c x_wc <= Capacity_w * y_w
    for w in warehouse_ids:
        model += (
            pulp.lpSum([x[(w, c)] for c in customer_ids]) <= wh_dict[w]["capacity"] * y[w],
            f"Capacity_Constraint_{w}",
        )

    # Optional Constraint 3: Max facilities to open
    if max_open_limit is not None and max_open_limit > 0:
        model += (
            pulp.lpSum([y[w] for w in warehouse_ids]) <= max_open_limit,
            "Max_Open_Facilities_Limit",
        )

    # Force open constraints
    for w in force_open_ids:
        if w in y:
            model += y[w] == 1, f"Force_Open_{w}"

    # Force closed constraints
    for w in force_closed_ids:
        if w in y:
            model += y[w] == 0, f"Force_Closed_{w}"

    # Solve with CBC
    solver = pulp.PULP_CBC_CMD(msg=False)
    status_code = model.solve(solver)
    status = pulp.LpStatus[status_code]

    total_fixed_cost = 0.0
    total_shipping_cost = 0.0
    open_facilities = []
    closed_facilities = []
    shipment_records = []

    if status == "Optimal":
        for w in warehouse_ids:
            is_open = int(round(pulp.value(y[w]) or 0.0)) == 1
            shipped_from_w = sum(
                pulp.value(x[(w, c)]) or 0.0
                for c in customer_ids
            )
            wh_info = wh_dict[w].copy()
            wh_info["is_open"] = is_open
            wh_info["utilized_capacity"] = round(shipped_from_w, 2)
            wh_info["slack_capacity"] = round(max(0.0, wh_info["capacity"] - shipped_from_w), 2)
            wh_info["utilization_pct"] = round(
                (shipped_from_w / wh_info["capacity"] * 100.0) if wh_info["capacity"] > 0 else 0.0, 1
            )

            if is_open:
                open_facilities.append(wh_info)
                total_fixed_cost += wh_info["fixed_cost"]
            else:
                closed_facilities.append(wh_info)

        for w in warehouse_ids:
            for c in customer_ids:
                flow_val = pulp.value(x[(w, c)])
                if flow_val and flow_val > 1e-4:
                    flow_val = round(float(flow_val), 2)
                    c_cost = cost_matrix[w][c]
                    tot = round(flow_val * c_cost, 2)
                    total_shipping_cost += tot
                    shipment_records.append({
                        "Warehouse_ID": w,
                        "Warehouse_Name": wh_dict[w]["name"],
                        "Customer_ID": c,
                        "Customer_Name": cust_dict[c]["name"],
                        "Units_Shipped": flow_val,
                        "Unit_Cost": c_cost,
                        "Total_Shipping_Cost": tot,
                    })

    facility_df = pd.DataFrame(open_facilities + closed_facilities)
    shipment_df = pd.DataFrame(shipment_records)

    # Customer coverage summary
    customer_summary = []
    for c in customer_ids:
        recv = sum(
            pulp.value(x[(w, c)]) or 0.0
            for w in warehouse_ids
        )
        customer_summary.append({
            "Customer_ID": c,
            "Customer_Name": cust_dict[c]["name"],
            "Demand": cust_dict[c]["demand"],
            "Received": round(recv, 2),
            "Status": "Satisfied" if recv >= cust_dict[c]["demand"] - 1e-4 else "Deficit",
        })
    customer_df = pd.DataFrame(customer_summary)

    total_cost = round(total_fixed_cost + total_shipping_cost, 2)

    return {
        "status": status,
        "is_optimal": (status == "Optimal"),
        "total_cost": total_cost,
        "fixed_cost": round(total_fixed_cost, 2),
        "shipping_cost": round(total_shipping_cost, 2),
        "open_facilities_count": len(open_facilities),
        "open_facilities": open_facilities,
        "closed_facilities": closed_facilities,
        "shipment_df": shipment_df,
        "facility_df": facility_df,
        "customer_df": customer_df,
    }
