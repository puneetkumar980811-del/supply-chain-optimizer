"""
Geospatial Map Visualizer using Folium.
Renders supply chain network topologies, shipping arcs, facility statuses,
and vehicle routing multi-stop tours on interactive OpenStreetMap tiles.
"""

import folium
from folium.plugins import BeautifyIcon


def create_network_map(plants, warehouses, customers, flows=None, center=(21.5, 78.5), zoom=5):
    """
    Creates an interactive Folium map showing the supply chain network:
    - Plants: Blue markers
    - Warehouses: Orange markers
    - Customers: Green markers
    - Active shipment arcs: Blue polylines with weight proportional to flow volume
    """
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")

    # Index coordinates
    coords = {}

    # 1. Plants
    for p in plants:
        coords[p["id"]] = (p["lat"], p["lon"])
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=9,
            popup=f"<b>Factory:</b> {p['name']}<br><b>Capacity:</b> {p.get('capacity', 'N/A')} Tons",
            tooltip=f"Factory: {p['name']}",
            color="#1e3a8a",
            fill=True,
            fill_color="#2563eb",
            fill_opacity=0.9,
        ).add_to(m)

    # 2. Warehouses
    for w in warehouses:
        coords[w["id"]] = (w["lat"], w["lon"])
        is_open = w.get("is_open", True)
        wh_color = "#16a34a" if is_open else "#dc2626"
        folium.Marker(
            location=[w["lat"], w["lon"]],
            popup=(
                f"<b>Warehouse:</b> {w['name']}<br>"
                f"<b>Status:</b> {'OPEN' if is_open else 'CLOSED'}<br>"
                f"<b>Capacity:</b> {w.get('capacity', 'N/A')} Tons<br>"
                f"<b>Fixed Cost:</b> ₹{w.get('fixed_cost', 0):,}"
            ),
            tooltip=f"Warehouse: {w['name']} ({'OPEN' if is_open else 'CLOSED'})",
            icon=folium.Icon(color="green" if is_open else "red", icon="home"),
        ).add_to(m)

    # 3. Customers
    for c in customers:
        coords[c["id"]] = (c["lat"], c["lon"])
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=7,
            popup=f"<b>Customer Market:</b> {c['name']}<br><b>Demand:</b> {c.get('demand', 'N/A')} Tons",
            tooltip=f"Market: {c['name']}",
            color="#b45309",
            fill=True,
            fill_color="#f59e0b",
            fill_opacity=0.85,
        ).add_to(m)

    # 4. Shipment Arcs
    if flows:
        # Determine max flow for proportional line weight
        max_flow = max([f.get("Flow_Units", f.get("flow", 1.0)) for f in flows], default=1.0)
        for f in flows:
            src = f.get("From", f.get("Warehouse_ID"))
            dst = f.get("To", f.get("Customer_ID"))
            qty = f.get("Flow_Units", f.get("Units_Shipped", f.get("flow", 0.0)))

            if src in coords and dst in coords and qty > 0.01:
                weight = 1.5 + (qty / max_flow) * 4.5
                folium.PolyLine(
                    locations=[coords[src], coords[dst]],
                    weight=weight,
                    color="#2563eb",
                    opacity=0.65,
                    tooltip=f"Shipment: {src} -> {dst} | {qty:.1f} Tons",
                ).add_to(m)

    return m


def create_vrp_route_map(depot, routes, center=None, zoom=6):
    """
    Renders multi-vehicle delivery tours on an interactive map.
    Each vehicle's route is drawn with a distinct color.
    """
    if center is None:
        center = (depot["lat"], depot["lon"])

    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")

    # Depot marker
    folium.Marker(
        location=[depot["lat"], depot["lon"]],
        popup=f"<b>CENTRAL DEPOT:</b> {depot['name']}",
        tooltip=f"Depot: {depot['name']}",
        icon=folium.Icon(color="black", icon="star"),
    ).add_to(m)

    palette = ["#dc2626", "#2563eb", "#16a34a", "#9333ea", "#ea580c", "#0891b2"]

    for idx, r in enumerate(routes):
        route_color = palette[idx % len(palette)]
        v_name = r["vehicle_id"]

        stops = r["stops"]
        poly_points = [[s["lat"], s["lon"]] for s in stops]

        # Draw vehicle route loop
        folium.PolyLine(
            locations=poly_points,
            weight=4,
            color=route_color,
            opacity=0.8,
            tooltip=f"{v_name}: {r['distance_km']} km | Cargo: {r['total_demand_delivered']} Tons",
        ).add_to(m)

        # Draw customer stop markers with sequence numbers
        for seq, s in enumerate(stops[1:-1], start=1):
            folium.CircleMarker(
                location=[s["lat"], s["lon"]],
                radius=8,
                popup=f"<b>Stop {seq} ({v_name}):</b> {s['name']}<br><b>Delivery:</b> {s['demand']} Tons",
                tooltip=f"Stop {seq}: {s['name']}",
                color=route_color,
                fill=True,
                fill_color=route_color,
                fill_opacity=0.9,
            ).add_to(m)

    return m
