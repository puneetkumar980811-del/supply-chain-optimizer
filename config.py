"""
Configuration and Global Constants for Supply Chain Optimizer (OptiChain)
College Mini-Project in Operations Research & Supply Chain Engineering.
"""

PROJECT_NAME = "OptiChain: Supply Chain Optimizer"
PROJECT_SUBTITLE = "Decision Support System for Network Optimization & Logistics Analytics"
COLLEGE_TAG = "Academic Mini-Project | Dept. of Computer Science & Engineering"
VERSION = "1.0.0"

# Currency and units
CURRENCY_SYMBOL = "₹"
WEIGHT_UNIT = "Tons"
DISTANCE_UNIT = "km"
CARBON_UNIT = "kg CO₂"

# Default Optimization Parameters
DEFAULT_CO2_COST_FACTOR = 0.05  # Carbon penalty per kg CO2
AVERAGE_TRUCK_CAPACITY = 20     # Tons per truck
CO2_PER_TON_KM = 0.082          # Heavy diesel truck average emission (kg CO2 / ton-km)

# UI Theme Custom CSS
CUSTOM_CSS = """
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    
    /* Header card */
    .project-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.12);
    }
    .project-header h1 {
        margin: 0;
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: white !important;
    }
    .project-header p {
        margin: 6px 0 0 0;
        font-size: 1.05rem;
        opacity: 0.92;
        color: #e0f2fe;
    }
    .project-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.22);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 10px;
        backdrop-filter: blur(4px);
    }

    /* Metric card styles */
    .metric-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        margin: 4px 0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Academic alert cards */
    .academic-callout {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        font-size: 0.92rem;
        color: #334155;
        margin-bottom: 16px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
</style>
"""
