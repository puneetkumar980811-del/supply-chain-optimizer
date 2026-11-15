"""
Plotly Chart Builders for Supply Chain Optimization Dashboards.
Includes Sankey flow diagrams, EOQ U-shaped cost trade-off curves,
scenario comparison bar charts, and time series forecast curves.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def build_sankey_flow(flow_df, source_col="From", target_col="To", value_col="Flow_Units"):
    """
    Builds an interactive Plotly Sankey diagram representing product flows
    from origins (e.g., Factories/Warehouses) to destinations (Customers).
    """
    if flow_df.empty or value_col not in flow_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No active shipment flows to display", showarrow=False)
        return fig

    sources = list(flow_df[source_col].unique())
    targets = list(flow_df[target_col].unique())
    all_nodes = sources + targets
    node_indices = {name: idx for idx, name in enumerate(all_nodes)}

    link_sources = [node_indices[src] for src in flow_df[source_col]]
    link_targets = [node_indices[tgt] for tgt in flow_df[target_col]]
    link_values = list(flow_df[value_col])

    # Distinct colors for origins (blue/teal) vs destinations (amber/orange)
    node_colors = ["#2563eb"] * len(sources) + ["#ea580c"] * len(targets)

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=18,
            thickness=22,
            line=dict(color="#1e293b", width=0.5),
            label=all_nodes,
            color=node_colors,
        ),
        link=dict(
            source=link_sources,
            target=link_targets,
            value=link_values,
            color="rgba(59, 130, 246, 0.45)",
            hovertemplate="From %{source.label}<br>To %{target.label}<br>Quantity: %{value:,.1f} Tons<extra></extra>",
        )
    )])

    fig.update_layout(
        title_text="Multi-Echelon Network Flow Distribution (Sankey)",
        font=dict(size=12, family="Inter, sans-serif"),
        height=450,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def build_eoq_curve_plot(curve_df, eoq_metrics):
    """
    Builds the classic Operations Research U-shaped Inventory Total Cost Curve.
    Highlights the optimal balance point where Holding Cost equals Ordering Cost.
    """
    optimal_q = eoq_metrics["eoq"]
    min_cost = eoq_metrics["total_relevant_cost"]

    fig = go.Figure()

    # Total Cost Curve (U-Shape)
    fig.add_trace(go.Scatter(
        x=curve_df["Order_Quantity"],
        y=curve_df["Total_Relevant_Cost"],
        mode="lines",
        name="Total Relevant Cost",
        line=dict(color="#2563eb", width=3),
    ))

    # Annual Holding Cost (Upward sloping line)
    fig.add_trace(go.Scatter(
        x=curve_df["Order_Quantity"],
        y=curve_df["Annual_Holding_Cost"],
        mode="lines",
        name="Annual Holding Cost (Q/2 * H)",
        line=dict(color="#10b981", width=2, dash="dash"),
    ))

    # Annual Ordering Cost (Downward sloping hyperbola)
    fig.add_trace(go.Scatter(
        x=curve_df["Order_Quantity"],
        y=curve_df["Annual_Ordering_Cost"],
        mode="lines",
        name="Annual Ordering Cost (D/Q * S)",
        line=dict(color="#f59e0b", width=2, dash="dot"),
    ))

    # Marker at Optimal EOQ
    fig.add_trace(go.Scatter(
        x=[optimal_q],
        y=[min_cost],
        mode="markers+text",
        name="Optimal EOQ (Q*)",
        marker=dict(color="#dc2626", size=14, symbol="star"),
        text=[f"EOQ: {optimal_q} units<br>Min Cost: ₹{min_cost:,.0f}"],
        textposition="top center",
    ))

    # Vertical line indicating optimal lot size
    fig.add_vline(x=optimal_q, line_width=1.5, line_dash="dash", line_color="#dc2626", opacity=0.7)

    fig.update_layout(
        title="Economic Order Quantity (EOQ) Cost Trade-Off Curve",
        xaxis_title="Order Quantity (Units per Order)",
        yaxis_title="Annual Inventory Cost (₹)",
        hovermode="x unified",
        template="plotly_white",
        height=450,
        legend=dict(yanchor="top", y=0.98, xanchor="right", x=0.98),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def build_forecast_plot(forecast_data):
    """
    Renders time-series demand forecasting with historical values,
    forecast projection, and 95% confidence bounds.
    """
    df = forecast_data["result_df"]
    best_name = forecast_data["best_model_name"]

    fig = go.Figure()

    # Historical Actual Demand
    fig.add_trace(go.Scatter(
        x=df["Period"],
        y=df["Actual_Demand"],
        mode="lines+markers",
        name="Historical Demand",
        line=dict(color="#0f172a", width=2.5),
        marker=dict(size=6),
    ))

    # Best Model Forecast
    fig.add_trace(go.Scatter(
        x=df["Period"],
        y=df["Best_Forecast"],
        mode="lines+markers",
        name=f"Best Model ({best_name})",
        line=dict(color="#2563eb", width=3, dash="dash"),
        marker=dict(size=7, symbol="diamond"),
    ))

    # 95% Confidence Interval Upper
    fig.add_trace(go.Scatter(
        x=df["Period"],
        y=df["CI_Upper_95"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # 95% Confidence Interval Lower with fill
    fig.add_trace(go.Scatter(
        x=df["Period"],
        y=df["CI_Lower_95"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(37, 99, 235, 0.15)",
        name="95% Confidence Band",
    ))

    fig.update_layout(
        title="Predictive Demand Curve with 95% Confidence Interval",
        xaxis_title="Time Period (Monthly)",
        yaxis_title="Demand Quantity (Units)",
        hovermode="x unified",
        template="plotly_white",
        height=450,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def build_scenario_comparison_bar(scenarios_list):
    """
    Compares baseline vs what-if disruption scenarios across total cost and unmet demand.
    scenarios_list: list of dicts [{'name': 'Baseline', 'cost': 120000, 'unmet': 0}, ...]
    """
    df = pd.DataFrame(scenarios_list)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["name"],
        y=df["cost"],
        name="Total Logistics Cost (₹)",
        marker_color="#3b82f6",
        text=[f"₹{c:,.0f}" for c in df["cost"]],
        textposition="auto",
    ))

    if "emissions_kg" in df.columns:
        fig.add_trace(go.Bar(
            x=df["name"],
            y=df["emissions_kg"],
            name="CO₂ Emissions (kg)",
            marker_color="#10b981",
            text=[f"{e:,.0f} kg" for e in df["emissions_kg"]],
            textposition="auto",
        ))

    fig.update_layout(
        title="Scenario Stress-Testing: Financial & Carbon Cost Impact",
        barmode="group",
        template="plotly_white",
        height=400,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig
