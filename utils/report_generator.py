"""
Academic and Executive Report Generator for OptiChain.
Exports formatted summary reports and downloadable CSV data.
"""

import pandas as pd
from datetime import datetime
from config import PROJECT_NAME, COLLEGE_TAG


def generate_executive_summary(
    transport_results=None,
    facility_results=None,
    inventory_results=None,
    vrp_results=None,
    forecast_results=None,
):
    """
    Generates a formal academic and management summary report in Markdown.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# {PROJECT_NAME} - Optimization Executive Summary
**Sub-title:** Automated Operations Research Decision Support System  
**Institution/Department:** {COLLEGE_TAG}  
**Generated On:** {timestamp}  

---

## 1. Executive Overview
This report presents optimal decision vectors computed by linear and mixed-integer mathematical models to minimize end-to-end supply chain operational costs, improve delivery efficiency, and minimize carbon footprints.

---
"""

    if transport_results:
        report += f"""
### 2. Multi-Echelon Transportation Optimization (LP)
- **Mathematical Solver:** PuLP Simplex / CBC Branch & Bound
- **Status:** {transport_results['status']}
- **Total Freight Logistics Cost:** ₹{transport_results['total_cost']:,.2f}
- **Total Carbon Footprint:** {transport_results['total_emissions_kg']:,.2f} kg CO₂
- **Total Supply Handled:** {transport_results['total_supply']:,.1f} Tons
- **Total Demand Fulfilled:** {transport_results['total_demand']:,.1f} Tons
- **System Balance:** {'Balanced Network' if transport_results['is_balanced'] else 'Unbalanced Network'}
"""

    if facility_results:
        report += f"""
### 3. Facility Location & Warehouse Selection (MILP)
- **Status:** {facility_results['status']}
- **Total Network Cost (Fixed + Shipping):** ₹{facility_results['total_cost']:,.2f}
- **Fixed Warehouse Operational Cost:** ₹{facility_results['fixed_cost']:,.2f}
- **Variable Secondary Transport Cost:** ₹{facility_results['shipping_cost']:,.2f}
- **Optimal Warehouses Opened:** {facility_results['open_facilities_count']} Distribution Centers
- **Recommended Open Locations:** {', '.join([w['name'] for w in facility_results['open_facilities']])}
"""

    if inventory_results:
        report += f"""
### 4. Inventory Analytics & Safety Stock Policy (EOQ / ROP)
- **Optimal Batch Order Quantity (EOQ):** {inventory_results['eoq']} units per order
- **Total Relevant Annual Inventory Cost:** ₹{inventory_results['total_relevant_cost']:,.2f}
- **Orders Placed Per Year:** {inventory_results['orders_per_year']} orders
- **Order Cycle Duration:** Every {inventory_results['cycle_time_days']} days
- **Recommended Safety Stock:** {inventory_results.get('safety_stock', 'N/A')} units
- **Target Service Level:** {inventory_results.get('service_level_pct', 95.0)}%
- **Reorder Point (ROP):** Place replenishment order when stock touches {inventory_results.get('reorder_point', 'N/A')} units
"""

    if vrp_results:
        report += f"""
### 5. Fleet Delivery Route Optimization (Capacitated VRP)
- **Fleet Size Deployed:** {vrp_results['vehicles_used']} delivery vehicles
- **Total Travel Distance:** {vrp_results['total_distance_km']:,.2f} km
- **Estimated Fuel Consumption:** {vrp_results['total_fuel_liters']:,.1f} Liters
- **Estimated Fuel Cost:** ₹{vrp_results['total_fuel_cost']:,.2f}
- **Estimated Carbon Emissions:** {vrp_results['total_co2_kg']:,.2f} kg CO₂
"""

    if forecast_results:
        report += f"""
### 6. Demand Forecasting Benchmark
- **Best Performing Algorithm:** {forecast_results['best_model_name']}
- **Projected Next-Cycle Monthly Demand:** {forecast_results['projected_demand']} units
- **Annualized Projected Volume:** {forecast_results['annual_projected_demand']} units
"""

    report += """
---
## 7. Viva Voce Key Takeaways
1. **Duality & Shadow Prices:** Supply constraints indicate marginal value of additional warehouse capacity.
2. **Trade-offs:** Holding vs. Ordering cost balance proves optimality at the EOQ minimum.
3. **Green Logistics:** Carbon weighting parameter allows multi-objective Pareto frontier exploration between cost and emissions.

*Report compiled automatically by OptiChain Decision Support Engine.*
"""
    return report


def convert_df_to_csv(df):
    """Encodes a DataFrame into UTF-8 CSV bytes for Streamlit download button."""
    return df.to_csv(index=False).encode("utf-8")
