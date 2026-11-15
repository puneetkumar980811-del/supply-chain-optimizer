"""
Capacitated Vehicle Routing Problem (CVRP) Solver.
Heuristic: Nearest Neighbor Allocation + 2-Opt Local Search Route Optimization.

Mathematical Formulation:
    Minimize Total Distance = SUM(k in Vehicles) SUM((i,j) in Route_k) Distance(i, j)
    Subject to:
        SUM(i in Route_k) Demand_i <= Vehicle_Capacity   for all vehicles k
        Each customer is visited exactly once
        All routes start and terminate at Depot (Node 0)
"""

import numpy as np
import pandas as pd
from data.sample_data import haversine_distance


def calculate_distance_matrix(locations):
    """
    Computes NxN pairwise Haversine distance matrix between all locations.
    locations : list of dicts with 'id', 'name', 'lat', 'lon'
    """
    n = len(locations)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dist_matrix[i][j] = haversine_distance(
                    locations[i]["lat"], locations[i]["lon"],
                    locations[j]["lat"], locations[j]["lon"]
                )
    return dist_matrix


def two_opt_swap(route, i, k):
    """Reverses the order of route segment between index i and k."""
    return route[:i] + route[i:k + 1][::-1] + route[k + 1:]


def two_opt_optimize(route, dist_matrix):
    """
    Applies the 2-Opt local search improvement heuristic to a single tour.
    Repeatedly swaps edges if doing so strictly decreases the route length.
    """
    best_route = route[:]
    improved = True
    max_iter = 100
    it = 0

    while improved and it < max_iter:
        improved = False
        it += 1
        for i in range(1, len(best_route) - 2):
            for k in range(i + 1, len(best_route) - 1):
                # Calculate change in distance: (i-1 -> i) and (k -> k+1) vs (i-1 -> k) and (i -> k+1)
                d_current = (
                    dist_matrix[best_route[i - 1]][best_route[i]]
                    + dist_matrix[best_route[k]][best_route[k + 1]]
                )
                d_new = (
                    dist_matrix[best_route[i - 1]][best_route[k]]
                    + dist_matrix[best_route[i]][best_route[k + 1]]
                )

                if d_new < d_current - 1e-4:
                    best_route = two_opt_swap(best_route, i, k)
                    improved = True
                    break
            if improved:
                break

    return best_route


def calculate_route_distance(route, dist_matrix):
    """Calculates total travel distance of a closed loop route."""
    d = 0.0
    for i in range(len(route) - 1):
        d += dist_matrix[route[i]][route[i + 1]]
    return round(float(d), 2)


def solve_cvrp(
    depot,
    customers,
    vehicle_capacity=1000,
    fuel_efficiency_km_per_l=3.5,
    fuel_cost_per_liter=95.0,
    co2_kg_per_liter=2.68,
):
    """
    Solves the Capacitated Vehicle Routing Problem for a fleet of vehicles.

    Parameters:
    -----------
    depot : dict
        {'id': 'D0', 'name': 'Central Depot', 'lat': ..., 'lon': ...}
    customers : list of dicts
        [{'id': 'C1', 'name': 'Market 1', 'lat': ..., 'lon': ..., 'demand': 150}, ...]
    vehicle_capacity : float
        Maximum capacity per vehicle in tons/units
    fuel_efficiency_km_per_l : float
        Vehicle mileage (km / liter)
    fuel_cost_per_liter : float
        Cost of fuel in ₹/L
    co2_kg_per_liter : float
        Carbon emissions produced per liter of diesel

    Returns:
    --------
    dict containing:
        - vehicle_routes: list of route details
        - total_distance_km: float
        - total_fuel_liters: float
        - total_fuel_cost: float
        - total_co2_kg: float
        - summary_df: pd.DataFrame
    """
    all_nodes = [depot] + customers
    n = len(all_nodes)
    dist_matrix = calculate_distance_matrix(all_nodes)

    unvisited = set(range(1, n))
    routes = []
    vehicle_id = 1

    while unvisited:
        curr_route = [0]
        curr_load = 0.0

        while unvisited:
            curr_node = curr_route[-1]
            # Find nearest customer that fits within vehicle capacity
            feasible_candidates = [
                c for c in unvisited
                if curr_load + all_nodes[c]["demand"] <= vehicle_capacity
            ]

            if not feasible_candidates:
                break  # Vehicle is full; return to depot

            # Pick nearest feasible customer
            nearest = min(feasible_candidates, key=lambda c: dist_matrix[curr_node][c])
            curr_route.append(nearest)
            curr_load += all_nodes[nearest]["demand"]
            unvisited.remove(nearest)

        # Return to depot
        curr_route.append(0)

        # Apply 2-Opt optimization to uncross paths
        optimized_route = two_opt_optimize(curr_route, dist_matrix)
        route_dist = calculate_route_distance(optimized_route, dist_matrix)

        # Build detailed stop list
        stop_details = []
        for stop_idx in optimized_route:
            node = all_nodes[stop_idx]
            stop_details.append({
                "id": node["id"],
                "name": node["name"],
                "lat": node["lat"],
                "lon": node["lon"],
                "demand": node.get("demand", 0),
            })

        fuel_used = round(route_dist / fuel_efficiency_km_per_l, 1)
        fuel_cost = round(fuel_used * fuel_cost_per_liter, 2)
        co2_emitted = round(fuel_used * co2_kg_per_liter, 2)

        routes.append({
            "vehicle_id": f"Vehicle-{vehicle_id}",
            "route_indices": optimized_route,
            "stops": stop_details,
            "total_demand_delivered": round(curr_load, 1),
            "capacity_utilization_pct": round((curr_load / vehicle_capacity) * 100.0, 1),
            "distance_km": route_dist,
            "fuel_liters": fuel_used,
            "fuel_cost": fuel_cost,
            "co2_emissions_kg": co2_emitted,
        })
        vehicle_id += 1

    total_dist = round(sum(r["distance_km"] for r in routes), 2)
    total_fuel = round(sum(r["fuel_liters"] for r in routes), 2)
    total_fuel_cost = round(sum(r["fuel_cost"] for r in routes), 2)
    total_co2 = round(sum(r["co2_emissions_kg"] for r in routes), 2)

    summary_rows = []
    for r in routes:
        stops_str = " -> ".join([s["name"] for s in r["stops"]])
        summary_rows.append({
            "Vehicle": r["vehicle_id"],
            "Stops Count": len(r["stops"]) - 2,
            "Cargo Delivered": r["total_demand_delivered"],
            "Capacity Util %": r["capacity_utilization_pct"],
            "Distance (km)": r["distance_km"],
            "Fuel (Liters)": r["fuel_liters"],
            "Fuel Cost (₹)": r["fuel_cost"],
            "CO₂ (kg)": r["co2_emissions_kg"],
            "Route Sequence": stops_str,
        })

    summary_df = pd.DataFrame(summary_rows)

    return {
        "vehicle_routes": routes,
        "total_distance_km": total_dist,
        "total_fuel_liters": total_fuel,
        "total_fuel_cost": total_fuel_cost,
        "total_co2_kg": total_co2,
        "vehicles_used": len(routes),
        "summary_df": summary_df,
    }
