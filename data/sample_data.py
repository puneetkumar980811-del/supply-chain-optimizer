"""
Realistic Sample Datasets for Supply Chain Optimization.
Includes Production Plants, Candidate Warehouses, Retail Markets,
GPS coordinates across India, cost matrices, and 24-month historical demand.
"""

import pandas as pd
import numpy as np

# 1. Production Plants (Supply Nodes)
PLANTS = [
    {"id": "P1", "name": "Mumbai Manufacturing Hub", "lat": 19.0760, "lon": 72.8777, "capacity": 1500, "prod_cost": 220},
    {"id": "P2", "name": "Chennai Industrial Plant", "lat": 13.0827, "lon": 80.2707, "capacity": 1200, "prod_cost": 210},
    {"id": "P3", "name": "Kolkata Mega Facility", "lat": 22.5726, "lon": 88.3639, "capacity": 1000, "prod_cost": 235},
    {"id": "P4", "name": "Delhi NCR Plant", "lat": 28.7041, "lon": 77.1025, "capacity": 1300, "prod_cost": 225},
]

# 2. Candidate Distribution Centers / Warehouses (Intermediate Nodes)
WAREHOUSES = [
    {"id": "W1", "name": "Pune Logistics Park", "lat": 18.5204, "lon": 73.8567, "capacity": 1100, "fixed_cost": 180000, "handling_cost": 15},
    {"id": "W2", "name": "Bengaluru Central Hub", "lat": 12.9716, "lon": 77.5946, "capacity": 1200, "fixed_cost": 200000, "handling_cost": 18},
    {"id": "W3", "name": "Nagpur Multi-Modal DC", "lat": 21.1458, "lon": 79.0882, "capacity": 1400, "fixed_cost": 160000, "handling_cost": 12},
    {"id": "W4", "name": "Ahmedabad Logistics Hub", "lat": 23.0225, "lon": 72.5714, "capacity": 950, "fixed_cost": 150000, "handling_cost": 14},
    {"id": "W5", "name": "Lucknow Regional Depot", "lat": 26.8467, "lon": 80.9462, "capacity": 1000, "fixed_cost": 140000, "handling_cost": 13},
]

# 3. Retail Demand Centers (Customers)
CUSTOMERS = [
    {"id": "C1", "name": "Hyderabad Market", "lat": 17.3850, "lon": 78.4867, "demand": 550},
    {"id": "C2", "name": "Jaipur Retail Hub", "lat": 26.9124, "lon": 75.7873, "demand": 420},
    {"id": "C3", "name": "Kochi Port Region", "lat": 9.9312, "lon": 76.2673, "demand": 380},
    {"id": "C4", "name": "Indore Commercial Area", "lat": 22.7196, "lon": 75.8577, "demand": 460},
    {"id": "C5", "name": "Patna Wholesale Center", "lat": 25.5941, "lon": 85.1376, "demand": 390},
    {"id": "C6", "name": "Chandigarh Distribution", "lat": 30.7333, "lon": 76.7794, "demand": 350},
    {"id": "C7", "name": "Bhubaneswar Trading Point", "lat": 20.2961, "lon": 85.8245, "demand": 320},
    {"id": "C8", "name": "Coimbatore Industrial Center", "lat": 11.0168, "lon": 76.9558, "demand": 340},
]


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two GPS coordinates in kilometers.
    Formula: Haversine equation.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2.0) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return round(float(R * c), 2)


def get_default_transport_costs():
    """
    Generate realistic cost matrix (Freight Cost per Ton in ₹)
    based on haversine distance plus base handling.
    """
    costs_plant_warehouse = {}
    for p in PLANTS:
        costs_plant_warehouse[p["id"]] = {}
        for w in WAREHOUSES:
            dist = haversine_distance(p["lat"], p["lon"], w["lat"], w["lon"])
            # Cost per ton = ₹80 base + ₹1.65 per km
            cost = round(80.0 + dist * 1.65, 2)
            costs_plant_warehouse[p["id"]][w["id"]] = cost

    costs_warehouse_customer = {}
    for w in WAREHOUSES:
        costs_warehouse_customer[w["id"]] = {}
        for c in CUSTOMERS:
            dist = haversine_distance(w["lat"], w["lon"], c["lat"], c["lon"])
            # Cost per ton = ₹60 base + ₹2.10 per km (secondary transport)
            cost = round(60.0 + dist * 2.10, 2)
            costs_warehouse_customer[w["id"]][c["id"]] = cost

    return costs_plant_warehouse, costs_warehouse_customer


def get_direct_plant_to_customer_costs():
    """
    Generate direct transportation cost matrix from Plants to Customers
    (for classic single-echelon Transportation Problem LP).
    """
    costs = {}
    for p in PLANTS:
        costs[p["id"]] = {}
        for c in CUSTOMERS:
            dist = haversine_distance(p["lat"], p["lon"], c["lat"], c["lon"])
            cost = round(100.0 + dist * 1.95, 2)
            costs[p["id"]][c["id"]] = cost
    return costs


def generate_demand_history(months=24, seed=42):
    """
    Generate synthetic 24-month historical demand time-series
    featuring trend, seasonality, and realistic stochastic noise.
    """
    np.random.seed(seed)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=months, freq="ME")
    
    # Baseline trend + seasonal sine wave + random noise
    t = np.arange(months)
    trend = 1200 + 18.5 * t
    seasonality = 180 * np.sin(2 * np.pi * t / 12) + 90 * np.cos(4 * np.pi * t / 12)
    noise = np.random.normal(0, 45, months)
    demand = np.maximum(500, np.round(trend + seasonality + noise))
    
    df = pd.DataFrame({
        "Month": dates.strftime("%Y-%m"),
        "Demand": demand.astype(int),
        "Promotion_Active": [1 if i % 4 == 0 else 0 for i in range(months)],
        "Fuel_Index": np.round(100 + 1.2 * t + np.random.normal(0, 2, months), 1)
    })
    return df
