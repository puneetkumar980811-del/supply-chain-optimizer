"""
OptiChain: Supply Chain Optimizer
College Mini-Project in Operations Research & Industrial Logistics.
Full interactive multi-module Streamlit Application.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_folium import st_folium

from config import (
    PROJECT_NAME,
    PROJECT_SUBTITLE,
    COLLEGE_TAG,
    CURRENCY_SYMBOL,
    CUSTOM_CSS,
)
from data.sample_data import (
    PLANTS,
    WAREHOUSES,
    CUSTOMERS,
    haversine_distance,
    get_default_transport_costs,
    get_direct_plant_to_customer_costs,
    generate_demand_history,
)
from models.transportation_lp import solve_transportation_problem
from models.facility_location import solve_facility_location
from models.inventory_eoq import (
    calculate_eoq,
    calculate_safety_stock_rop,
    generate_eoq_cost_curve,
)
from models.vrp_router import solve_cvrp
from models.demand_forecaster import run_comprehensive_forecast
from utils.chart_builder import (
    build_sankey_flow,
    build_eoq_curve_plot,
    build_forecast_plot,
    build_scenario_comparison_bar,
)
from utils.map_visualizer import create_network_map, create_vrp_route_map
from utils.report_generator import generate_executive_summary, convert_df_to_csv

# Configure Streamlit page
st.set_page_config(
    page_title="OptiChain - Supply Chain Optimizer",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Top Banner
st.markdown(
    f"""
    <div class="project-header">
        <h1>📦 {PROJECT_NAME}</h1>
        <p>{PROJECT_SUBTITLE}</p>
        <span class="project-badge">🎓 {COLLEGE_TAG}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar Navigation
st.sidebar.image(
    "https://img.icons8.com/fluency/96/supply-chain.png",
    width=70,
)
st.sidebar.title("Navigation")
menu_selection = st.sidebar.radio(
    "Select Optimization Module:",
    [
        "🏭 Transportation LP",
        "🏢 Facility Location (MILP)",
        "📦 Inventory & Safety Stock (EOQ)",
        "🚚 Vehicle Route Optimization (VRP)",
        "📈 Demand Forecasting",
        "⚡ What-If Disruption Simulator",
        "🎓 Academic Theory & Viva Guide",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Global Parameters")
green_weight = st.sidebar.slider(
    "Green ESG Carbon Weight (₹/kg CO₂)",
    min_value=0.0,
    max_value=2.0,
    value=0.05,
    step=0.01,
    help="Higher values penalize carbon emissions to favor eco-friendly shorter logistics routes.",
)

# Cache historical demand data in session state
if "demand_history_df" not in st.session_state:
    st.session_state["demand_history_df"] = generate_demand_history(months=24)


# ==============================================================================
# MODULE 1: TRANSPORTATION PROBLEM (LINEAR PROGRAMMING)
# ==============================================================================
if menu_selection == "🏭 Transportation LP":
    st.subheader("🏭 Multi-Source Transportation Problem Optimization")
    st.markdown(
        """
        <div class="academic-callout">
            <b>Mathematical Formulation (Simplex LP):</b><br>
            Minimize <i>Z</i> = &sum;<sub><i>i</i></sub> &sum;<sub><i>j</i></sub> <i>c<sub>ij</sub> &times; x<sub>ij</sub></i> + &lambda; &times; Carbon Penalties<br>
            Subject to: Supply Capacity Constraints (&sum;<sub><i>j</i></sub> <i>x<sub>ij</sub> &le; S<sub>i</sub></i>) 
            and Customer Demand Satisfaction (&sum;<sub><i>i</i></sub> <i>x<sub>ij</sub> &ge; D<sub>j</sub></i>).
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_cfg1, col_cfg2 = st.columns([1, 2])

    with col_cfg1:
        st.markdown("#### Supply & Demand Adjustments")
        supply_overrides = {}
        with st.expander("🏭 Factory Capacities (Tons)", expanded=True):
            for p in PLANTS:
                supply_overrides[p["id"]] = st.number_input(
                    f"{p['name']}",
                    min_value=0,
                    max_value=3000,
                    value=p["capacity"],
                    step=50,
                    key=f"trans_sup_{p['id']}",
                )

        demand_overrides = {}
        with st.expander("🛒 Customer Demand Requirements (Tons)", expanded=False):
            for c in CUSTOMERS:
                demand_overrides[c["id"]] = st.number_input(
                    f"{c['name']}",
                    min_value=0,
                    max_value=2000,
                    value=c["demand"],
                    step=25,
                    key=f"trans_dem_{c['id']}",
                )

    # Calculate distance matrix for plants to customers
    direct_costs = get_direct_plant_to_customer_costs()
    dist_matrix = {}
    for p in PLANTS:
        dist_matrix[p["id"]] = {}
        for c in CUSTOMERS:
            dist_matrix[p["id"]][c["id"]] = haversine_distance(p["lat"], p["lon"], c["lat"], c["lon"])

    # Solve Optimization
    res = solve_transportation_problem(
        supply_overrides,
        demand_overrides,
        direct_costs,
        distance_matrix=dist_matrix,
        emission_weight=green_weight,
    )

    with col_cfg2:
        st.markdown("#### Optimal Solution Key Performance Indicators")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Freight Cost", f"{CURRENCY_SYMBOL}{res['total_cost']:,.0f}")
        kpi2.metric("CO₂ Emissions", f"{res['total_emissions_kg']:,.0f} kg")
        kpi3.metric("System Balance", "Balanced" if res["is_balanced"] else "Unbalanced")
        kpi4.metric("Solver Status", res["status"])

        # Tabbed visualizers
        tab_flow, tab_map, tab_tables = st.tabs(["📊 Network Flow (Sankey)", "🗺️ Geospatial Map", "📋 Allocation Tables"])

        with tab_flow:
            if not res["flow_df"].empty:
                sankey_fig = build_sankey_flow(res["flow_df"], source_col="From", target_col="To", value_col="Flow_Units")
                st.plotly_chart(sankey_fig, use_container_width=True)
            else:
                st.warning("No shipment flow generated.")

        with tab_map:
            st.info("Interactive map displaying factory nodes (blue), customer markets (amber), and optimal shipping routes.")
            net_map = create_network_map(PLANTS, [], CUSTOMERS, flows=res["flows"])
            st_folium(net_map, width="100%", height=450)

        with tab_tables:
            st.markdown("##### Optimal Shipment Flows")
            st.dataframe(res["flow_df"], use_container_width=True)

            sub_c1, sub_c2 = st.columns(2)
            with sub_c1:
                st.markdown("##### Supply Hub Capacity Utilization")
                st.dataframe(res["supply_summary"], use_container_width=True)
            with sub_c2:
                st.markdown("##### Demand Fulfillment Summary")
                st.dataframe(res["demand_summary"], use_container_width=True)

            st.download_button(
                "📥 Download Shipment Flow CSV",
                data=convert_df_to_csv(res["flow_df"]),
                file_name="optimal_shipment_flows.csv",
                mime="text/csv",
            )


# ==============================================================================
# MODULE 2: FACILITY LOCATION & WAREHOUSE SELECTION (MILP)
# ==============================================================================
elif menu_selection == "🏢 Facility Location (MILP)":
    st.subheader("🏢 Capacitated Facility Location & Warehouse Selection (MILP)")
    st.markdown(
        """
        <div class="academic-callout">
            <b>Mathematical Formulation (Mixed-Integer Linear Programming):</b><br>
            Minimize <i>Z</i> = &sum;<sub><i>w</i></sub> <i>F<sub>w</sub> &times; y<sub>w</sub></i> + &sum;<sub><i>w</i></sub> &sum;<sub><i>c</i></sub> <i>c<sub>wc</sub> &times; x<sub>wc</sub></i><br>
            Subject to: <i>y<sub>w</sub> &isin; {0, 1}</i> (binary decision to open/close DC <i>w</i>), and capacity link &sum;<sub><i>c</i></sub> <i>x<sub>wc</sub> &le; Cap<sub>w</sub> &times; y<sub>w</sub></i>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_side, col_main = st.columns([1, 2])

    with col_side:
        st.markdown("#### Candidate Warehouses & Controls")
        max_open = st.slider("Max Allowed Open Facilities (p-Limit)", min_value=1, max_value=len(WAREHOUSES), value=3)

        force_open = []
        force_closed = []
        st.markdown("##### Manual Overrides:")
        for w in WAREHOUSES:
            choice = st.selectbox(
                f"{w['name']}",
                options=["Optimizer Decides", "Force OPEN", "Force CLOSED"],
                index=0,
                key=f"fl_{w['id']}",
            )
            if choice == "Force OPEN":
                force_open.append(w["id"])
            elif choice == "Force CLOSED":
                force_closed.append(w["id"])

    # Get secondary transport costs
    _, wh_cust_costs = get_default_transport_costs()

    fl_res = solve_facility_location(
        candidate_warehouses=WAREHOUSES,
        customers=CUSTOMERS,
        cost_matrix=wh_cust_costs,
        max_open_limit=max_open,
        force_open_ids=force_open,
        force_closed_ids=force_closed,
    )

    with col_main:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Logistics Cost", f"{CURRENCY_SYMBOL}{fl_res['total_cost']:,.0f}")
        m2.metric("Fixed Setup Cost", f"{CURRENCY_SYMBOL}{fl_res['fixed_cost']:,.0f}")
        m3.metric("Shipping Freight Cost", f"{CURRENCY_SYMBOL}{fl_res['shipping_cost']:,.0f}")
        m4.metric("Open Facilities", f"{fl_res['open_facilities_count']} of {len(WAREHOUSES)}")

        tab_fl_map, tab_fl_alloc, tab_fl_summary = st.tabs(["🗺️ Geographic Map", "📊 Flow Allocations", "📋 Facility Status"])

        with tab_fl_map:
            # Prepare warehouse list with is_open tag
            open_wh_ids = {w["id"] for w in fl_res["open_facilities"]}
            wh_for_map = []
            for w in WAREHOUSES:
                w_copy = w.copy()
                w_copy["is_open"] = (w["id"] in open_wh_ids)
                wh_for_map.append(w_copy)

            st.info("Map displaying candidate warehouses: Green = OPEN, Red = CLOSED.")
            fl_map = create_network_map([], wh_for_map, CUSTOMERS, flows=fl_res["shipment_df"].to_dict("records"))
            st_folium(fl_map, width="100%", height=450)

        with tab_fl_alloc:
            st.dataframe(fl_res["shipment_df"], use_container_width=True)

        with tab_fl_summary:
            st.dataframe(fl_res["facility_df"], use_container_width=True)


# ==============================================================================
# MODULE 3: INVENTORY OPTIMIZATION & SAFETY STOCK (EOQ & ROP)
# ==============================================================================
elif menu_selection == "📦 Inventory & Safety Stock (EOQ)":
    st.subheader("📦 Inventory Optimization & Safety Stock Analytics")
    st.markdown(
        """
        <div class="academic-callout">
            <b>Mathematical Formulas:</b><br>
            &bull; Economic Order Quantity: <i>Q*</i> = &radic;(2<i>DS / H</i>)<br>
            &bull; Reorder Point (ROP): <i>ROP</i> = (<i>d &times; L</i>) + <i>Z<sub>&alpha;</sub> &times; &sigma;<sub>L</sub></i><br>
            At the optimal lot size <i>Q*</i>, annual holding cost strictly equals annual ordering cost.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        annual_demand = st.number_input("Annual Demand (Units/Year)", min_value=100, max_value=500000, value=15000, step=500)
        order_cost = st.number_input("Order Setup Cost (₹/Order)", min_value=10.0, max_value=10000.0, value=350.0, step=25.0)
    with c2:
        unit_price = st.number_input("Unit Purchase Price (₹)", min_value=1.0, max_value=100000.0, value=120.0, step=10.0)
        holding_pct = st.slider("Annual Holding Cost (% of Price)", min_value=5.0, max_value=50.0, value=20.0, step=1.0)
    with c3:
        lead_time = st.number_input("Supplier Lead Time (Days)", min_value=1, max_value=90, value=10, step=1)
        service_lvl = st.select_slider(
            "Cycle Service Level (Z-Factor)",
            options=[0.90, 0.95, 0.98, 0.99, 0.999],
            value=0.95,
            format_func=lambda x: f"{x*100:.1f}% Service Level",
        )

    curve_df, eoq_res = generate_eoq_cost_curve(annual_demand, order_cost, unit_price, holding_pct)
    rop_res = calculate_safety_stock_rop(annual_demand, lead_time, service_level=service_lvl)

    # Metric Row
    e1, e2, e3, e4, e5 = st.columns(5)
    e1.metric("Optimal EOQ (Q*)", f"{eoq_res['eoq']:,.0f} units")
    e2.metric("Total Relevant Cost", f"{CURRENCY_SYMBOL}{eoq_res['total_relevant_cost']:,.0f}")
    e3.metric("Orders / Year", f"{eoq_res['orders_per_year']}")
    e4.metric("Safety Stock", f"{rop_res['safety_stock']:,.0f} units")
    e5.metric("Reorder Point (ROP)", f"{rop_res['reorder_point']:,.0f} units")

    # Plot Cost Curve
    cost_curve_fig = build_eoq_curve_plot(curve_df, eoq_res)
    st.plotly_chart(cost_curve_fig, use_container_width=True)

    # Interactive Inventory Health Checker
    st.markdown("---")
    st.markdown("#### 🔍 Real-Time Warehouse Inventory Health Checker")
    curr_stock = st.number_input("Enter Current Stock Level in Warehouse (Units):", min_value=0, max_value=50000, value=int(rop_res["reorder_point"] * 1.2), step=50)

    if curr_stock < rop_res["safety_stock"]:
        st.error(f"🚨 **CRITICAL STOCKOUT RISK!** Current stock ({curr_stock}) is below Safety Stock ({rop_res['safety_stock']}). Trigger emergency replenishment immediately!")
    elif curr_stock <= rop_res["reorder_point"]:
        st.warning(f"⚠️ **REORDER TRIGGERED!** Current stock ({curr_stock}) is at/below Reorder Point ({rop_res['reorder_point']}). Place an order of **{eoq_res['eoq']} units**.")
    elif curr_stock > rop_res["reorder_point"] + eoq_res["eoq"]:
        st.info(f"📦 **OVERSTOCKED!** Current stock ({curr_stock}) exceeds maximum inventory buffer. High carrying costs incurred.")
    else:
        st.success(f"✅ **HEALTHY INVENTORY BUFFER!** Stock level ({curr_stock}) is adequate. Next order expected when stock drops to {rop_res['reorder_point']} units.")


# ==============================================================================
# MODULE 4: VEHICLE ROUTE OPTIMIZATION (CAPACITATED VRP)
# ==============================================================================
elif menu_selection == "🚚 Vehicle Route Optimization (VRP)":
    st.subheader("🚚 Capacitated Vehicle Routing Problem (CVRP) with 2-Opt Heuristic")
    st.markdown(
        """
        <div class="academic-callout">
            <b>Operations Research Heuristic:</b><br>
            Greedy Nearest Neighbor clustering creates initial delivery routes satisfying vehicle capacity constraints.<br>
            <b>2-Opt Local Search Improvement</b> iteratively uncrosses route arcs to eliminate distance waste and reduce carbon emissions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    vrp_c1, vrp_c2 = st.columns([1, 2])

    with vrp_c1:
        st.markdown("#### Fleet & Routing Parameters")
        depot_choice = st.selectbox(
            "Select Origin Depot:",
            options=[w["name"] for w in WAREHOUSES],
            index=2,  # Nagpur central hub
        )
        selected_depot = next(w for w in WAREHOUSES if w["name"] == depot_choice)

        v_capacity = st.slider("Vehicle Payload Capacity (Tons)", min_value=200, max_value=2000, value=750, step=50)
        fuel_price = st.number_input("Diesel Fuel Price (₹/Liter)", min_value=50.0, max_value=150.0, value=94.5, step=0.5)

    vrp_res = solve_cvrp(
        depot=selected_depot,
        customers=CUSTOMERS,
        vehicle_capacity=v_capacity,
        fuel_cost_per_liter=fuel_price,
    )

    with vrp_c2:
        st.markdown("#### Fleet Routing KPI Performance")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Vehicles Deployed", f"{vrp_res['vehicles_used']} trucks")
        k2.metric("Total Route Distance", f"{vrp_res['total_distance_km']:,.0f} km")
        k3.metric("Fleet Fuel Cost", f"{CURRENCY_SYMBOL}{vrp_res['total_fuel_cost']:,.0f}")
        k4.metric("CO₂ Emissions", f"{vrp_res['total_co2_kg']:,.0f} kg")

        st.info("Interactive delivery route map with vehicle color coding.")
        v_map = create_vrp_route_map(selected_depot, vrp_res["vehicle_routes"])
        st_folium(v_map, width="100%", height=450)

    st.markdown("##### Detailed Fleet Turn-by-Turn Itinerary")
    st.dataframe(vrp_res["summary_df"], use_container_width=True)


# ==============================================================================
# MODULE 5: DEMAND FORECASTING ENGINE
# ==============================================================================
elif menu_selection == "📈 Demand Forecasting":
    st.subheader("📈 Time-Series Demand Forecasting & Error Benchmarking")
    st.markdown(
        """
        <div class="academic-callout">
            <b>Predictive Analytics Engine:</b><br>
            Evaluates multiple forecasting algorithms (Simple Moving Average, Single Exponential Smoothing, 
            Holt's Double Exponential Trend, Linear Regression) across standard accuracy benchmarks (MAE, RMSE, MAPE).
        </div>
        """,
        unsafe_allow_html=True,
    )

    fc_col1, fc_col2 = st.columns([1, 2])

    with fc_col1:
        st.markdown("#### Forecasting Configuration")
        fc_horizon = st.slider("Forecast Horizon (Months Ahead)", min_value=1, max_value=12, value=6)

        st.markdown("##### Historical Demand Data")
        hist_df = st.session_state["demand_history_df"]
        st.dataframe(hist_df.tail(8), use_container_width=True)

    fc_res = run_comprehensive_forecast(hist_df, forecast_periods=fc_horizon)

    with fc_col2:
        m_best, m_proj, m_ann = st.columns(3)
        m_best.metric("Top Ranked Algorithm", fc_res["best_model_name"])
        m_proj.metric("Next-Month Projected Demand", f"{fc_res['projected_demand']} units")
        m_ann.metric("Annualized Demand", f"{fc_res['annual_projected_demand']:,.0f} units")

        fc_fig = build_forecast_plot(fc_res)
        st.plotly_chart(fc_fig, use_container_width=True)

    st.markdown("#### Model Error Benchmarks (Lower is Better)")
    st.dataframe(fc_res["metrics_df"].style.highlight_min(axis=0, color="#bbf7d0"), use_container_width=True)


# ==============================================================================
# MODULE 6: WHAT-IF DISRUPTION SIMULATOR
# ==============================================================================
elif menu_selection == "⚡ What-If Disruption Simulator":
    st.subheader("⚡ Supply Chain Stress-Testing & Disruption Simulator")
    st.markdown(
        """
        <div class="academic-callout">
            Simulate real-world supply chain crises (fuel price spikes, major factory strikes, sudden demand surges)
            and evaluate how the Linear Programming engine dynamically reroutes logistics to minimize total cost.
        </div>
        """,
        unsafe_allow_html=True,
    )

    sim_c1, sim_c2 = st.columns([1, 2])

    with sim_c1:
        st.markdown("#### Crisis Scenarios")
        scenario_type = st.radio(
            "Select Disruption Event:",
            [
                "Baseline (Normal Operations)",
                "Scenario A: Fuel Price Shock (+50%)",
                "Scenario B: Factory Shutdown (Mumbai Plant Struck)",
                "Scenario C: Festive Demand Surge (+40% Demand)",
                "Scenario D: Dual Catastrophe (Shutdown + Fuel Spike)",
            ],
        )

    # Base setup
    base_supply = {p["id"]: p["capacity"] for p in PLANTS}
    base_demand = {c["id"]: c["demand"] for c in CUSTOMERS}
    base_costs = get_direct_plant_to_customer_costs()
    dist_matrix = {
        p["id"]: {c["id"]: haversine_distance(p["lat"], p["lon"], c["lat"], c["lon"]) for c in CUSTOMERS}
        for p in PLANTS
    }

    # Solve Baseline
    base_res = solve_transportation_problem(base_supply, base_demand, base_costs, dist_matrix)

    # Apply Disruption Parameters
    disrupted_supply = base_supply.copy()
    disrupted_demand = base_demand.copy()
    disrupted_costs = {p: c.copy() for p, c in base_costs.items()}

    if "Fuel Price Shock" in scenario_type or "Dual Catastrophe" in scenario_type:
        for p in disrupted_costs:
            for c in disrupted_costs[p]:
                disrupted_costs[p][c] = round(disrupted_costs[p][c] * 1.5, 2)

    if "Factory Shutdown" in scenario_type or "Dual Catastrophe" in scenario_type:
        disrupted_supply["P1"] = 0  # Mumbai plant goes offline

    if "Festive Demand Surge" in scenario_type:
        for c in disrupted_demand:
            disrupted_demand[c] = int(round(disrupted_demand[c] * 1.4))

    disrupted_res = solve_transportation_problem(
        disrupted_supply,
        disrupted_demand,
        disrupted_costs,
        dist_matrix,
    )

    with sim_c2:
        cost_delta = disrupted_res["total_cost"] - base_res["total_cost"]
        cost_delta_pct = (cost_delta / base_res["total_cost"] * 100.0) if base_res["total_cost"] > 0 else 0.0

        d1, d2, d3 = st.columns(3)
        d1.metric("Baseline Cost", f"{CURRENCY_SYMBOL}{base_res['total_cost']:,.0f}")
        d2.metric("Disrupted Cost", f"{CURRENCY_SYMBOL}{disrupted_res['total_cost']:,.0f}", delta=f"{cost_delta_pct:+.1f}%", delta_color="inverse")
        d3.metric("Unmet Customer Demand", f"{disrupted_res['demand_summary']['Unmet'].sum():,.0f} Tons")

        # Bar chart comparison
        scenarios_payload = [
            {"name": "Normal Baseline", "cost": base_res["total_cost"], "emissions_kg": base_res["total_emissions_kg"]},
            {"name": scenario_type, "cost": disrupted_res["total_cost"], "emissions_kg": disrupted_res["total_emissions_kg"]},
        ]
        comp_bar = build_scenario_comparison_bar(scenarios_payload)
        st.plotly_chart(comp_bar, use_container_width=True)

    st.markdown("##### Rerouted Shipment Allocations Under Crisis")
    st.dataframe(disrupted_res["flow_df"], use_container_width=True)


# ==============================================================================
# MODULE 7: ACADEMIC THEORY & VIVA VOCE GUIDE
# ==============================================================================
elif menu_selection == "🎓 Academic Theory & Viva Guide":
    st.subheader("🎓 Academic Project Theory & Viva Voce Guide")
    st.markdown(
        """
        This section provides direct academic explanations, mathematical formulations,
        and examiner viva-voce questions designed for top grades in university project defenses.
        """
    )

    tab_theory, tab_viva, tab_report = st.tabs([
        "📖 Mathematical Formulations",
        "🎯 Viva Voce Q&A (30+ Questions)",
        "📄 Download Project Report & Slides",
    ])

    with tab_theory:
        st.markdown(
            r"""
            ### 1. The Classical Transportation Problem
            Given $m$ supply centers and $n$ demand centers:
            $$\min Z = \sum_{i=1}^{m} \sum_{j=1}^{n} c_{ij} x_{ij}$$
            Subject to:
            $$\sum_{j=1}^{n} x_{ij} \le S_i \quad \forall i=1,\dots,m \quad \text{(Supply Capacity)}$$
            $$\sum_{i=1}^{m} x_{ij} \ge D_j \quad \forall j=1,\dots,n \quad \text{(Demand Satisfaction)}$$
            $$x_{ij} \ge 0$$

            ### 2. Capacitated Facility Location (MILP)
            $$\min Z = \sum_{w=1}^{W} F_w y_w + \sum_{w=1}^{W}\sum_{c=1}^{C} c_{wc} x_{wc}$$
            Subject to:
            $$\sum_{w=1}^{W} x_{wc} \ge D_c \quad \forall c$$
            $$\sum_{c=1}^{C} x_{wc} \le Cap_w \cdot y_w \quad \forall w$$
            $$y_w \in \{0, 1\}, \quad x_{wc} \ge 0$$

            ### 3. Economic Order Quantity & Safety Stock
            $$Q^* = \sqrt{\frac{2DS}{H}}, \qquad \text{ROP} = (\bar{d} \times L) + Z_{\alpha}\sigma_L$$
            """
        )

    with tab_viva:
        st.markdown(
            """
            ### Top Viva Voce Questions & Answers

            **Q1: What is the core difference between Linear Programming (LP) and Mixed-Integer Linear Programming (MILP)?**  
            *Answer:* In LP, all decision variables are continuous (can take fractional values). In MILP, some variables are constrained to take integer or binary values (like $y_w \\in \\{0, 1\\}$ for opening or closing a warehouse). MILP is NP-hard and solved via Branch & Bound / Cutting Plane algorithms.

            **Q2: What is degeneracy in the Transportation Problem, and how does the Simplex algorithm handle it?**  
            *Answer:* Degeneracy occurs when the number of basic variables in a basic feasible solution is strictly less than $(m + n - 1)$. In such cases, an infinitesimal allocation $\\epsilon > 0$ is placed in an independent cell to prevent cycling and allow dual multipliers ($u_i, v_j$) to be calculated.

            **Q3: Why does Holding Cost equal Ordering Cost at the optimal EOQ?**  
            *Answer:* Total relevant cost $TC = \\frac{D}{Q}S + \\frac{Q}{2}H$. Taking the first derivative with respect to $Q$ and setting it to zero: $-\\frac{DS}{Q^2} + \\frac{H}{2} = 0 \\implies \\frac{DS}{Q} = \\frac{QH}{2}$. Thus, annual ordering cost exactly balances annual holding cost at the minimum cost point.

            **Q4: How does 2-Opt local search improve vehicle routes?**  
            *Answer:* 2-Opt selects two non-adjacent edges in a tour $(i, i+1)$ and $(j, j+1)$ and tests if reconnecting them as $(i, j)$ and $(i+1, j+1)$ reduces total Euclidean/Haversine distance by uncrossing intersecting paths.
            """
        )

    with tab_report:
        st.markdown("### Export Project Documentation")
        exec_summary = generate_executive_summary()
        st.download_button(
            "📥 Download Executive Summary (Markdown)",
            data=exec_summary,
            file_name="OptiChain_Executive_Summary.md",
            mime="text/markdown",
        )
        st.info("Full project report is also available in the `docs/PROJECT_REPORT.md` file in the project directory.")
