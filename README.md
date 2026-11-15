<<<<<<< HEAD
# 🚚 OptiChain: Supply Chain Optimizer
**Decision Support System for Network Optimization & Logistics Analytics**  
*College Mini-Project | Operations Research, Linear Programming & Heuristic Analytics*

---

## 🌟 Overview
**OptiChain** is a comprehensive, production-grade academic mini-project designed for engineering and management students. It bridges mathematical theory (Linear Programming, Mixed-Integer Linear Programming, Stochastic Inventory Theory, and Combinatorial Heuristics) with an interactive web dashboard.

Whether you are preparing for a **university mini-project submission**, a **viva-voce defense**, or a **technical seminar**, OptiChain provides end-to-end functionality, academic documentation, and live simulation capabilities.

---

## 🚀 Key Modules & Capabilities

| Module | Mathematical Formulation | Algorithm & Tool | Core Output |
| :--- | :--- | :--- | :--- |
| **1. Transportation LP** | Multi-source, multi-destination LP | Simplex / PuLP CBC | Optimal shipment flows, Sankey diagram, $CO_2$ emissions |
| **2. Facility Location (MILP)** | Capacitated Facility Location | Branch & Bound / MILP | Optimal open warehouses, fixed vs variable cost balance |
| **3. Inventory & Safety Stock** | Classical EOQ & Stochastic ROP | SciPy / Normal Distribution | U-shaped cost curve, optimal batch size, health checker |
| **4. Vehicle Routing (CVRP)** | Capacitated Routing Problem | Nearest Neighbor + 2-Opt | Multi-stop delivery routes, fuel cost, distance reduction |
| **5. Demand Forecasting** | Time-series forecasting | SMA, SES, Holt's Trend, OLS | 6-month projected demand, 95% confidence intervals, MAPE |
| **6. Disruption Simulator** | Stress-testing under crisis | Real-time LP re-optimization | Cost delta under fuel shocks, plant outages, demand surges |
| **7. Theory & Viva Prep** | University defense guide | Comprehensive Markdown | 35+ Viva Q&A, LaTeX formulas, 10-slide seminar outline |

---

## 📂 Project Directory Structure

```
spl/
├── app.py                         # Multi-page interactive Streamlit dashboard
├── config.py                      # Global constants, UI themes, and college branding
├── run.bat                        # Windows one-click launcher
├── OptiChain_Presentation.pptx    # Complete 12-slide PowerPoint presentation (16:9 Widescreen)
├── presentation.html              # Interactive browser slideshow with fullscreen & print to PDF
├── generate_ppt.py                # Python script to regenerate .pptx presentation
├── requirements.txt               # Python dependencies
├── models/
│   ├── transportation_lp.py       # Transportation Problem solver (PuLP LP)
│   ├── facility_location.py       # Capacitated Facility Location solver (PuLP MILP)
│   ├── inventory_eoq.py           # EOQ, Safety Stock, and ROP analytics
│   ├── vrp_router.py              # Capacitated Vehicle Routing Problem (2-Opt)
│   └── demand_forecaster.py       # Time-series forecasting models & error metrics
├── data/
│   ├── sample_data.py             # Realistic Indian supply chain topology & historical demand
├── utils/
│   ├── chart_builder.py           # Plotly charts (Sankey, EOQ curve, Forecast, Scenarios)
│   ├── map_visualizer.py          # Folium geospatial network and vehicle tour maps
│   └── report_generator.py        # Executive summary generator & CSV export
├── tests/
│   └── test_optimizers.py         # Automated pytest unit tests (100% passing)
└── docs/
    ├── PRESENTATION_SPEAKER_NOTES.md # Word-for-word spoken script for Shezan, Asif & Puneet
    ├── PROJECT_REPORT.md          # Full university academic project report
    ├── VIVA_QUESTIONS.md          # 35+ Viva Voce questions & answers
    └── PPT_SLIDES_OUTLINE.md      # 10-slide seminar presentation outline
```

---

## 👥 Project Team
- **Shezan Abbas**: Linear Programming (LP), PuLP Simplex Solver, Green Logistics ESG Carbon Penalty ($\lambda$), System Architecture.
- **Asif Khan**: Mixed-Integer Linear Programming (MILP), Facility Location Model, Stochastic Inventory Theory (EOQ & Safety Stock).
- **Puneet Kumar**: Capacitated Vehicle Routing (CVRP with 2-Opt), Time-Series Demand Forecasting, What-If Disruption Simulator.

---

## ⚡ Quick Start

### Option 1: One-Click Windows Launcher
Double-click `run.bat` in the project folder.

### Option 2: Command Line
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run automated test suite
pytest tests/test_optimizers.py -v

# 3. Launch interactive Streamlit dashboard
python -m streamlit run app.py
```
The dashboard will open automatically at `http://localhost:8501`.

---

## 🎓 Academic Defense Resources
Inside the `docs/` folder:
- **`PROJECT_REPORT.md`**: Formal academic project report ready for university submission (includes Abstract, Formulations, Architecture Diagram, Results, and References).
- **`VIVA_QUESTIONS.md`**: 35+ Viva Voce questions covering Duality, Simplex, Degeneracy, Branch & Bound, EOQ derivations, and 2-Opt complexity.
- **`PPT_SLIDES_OUTLINE.md`**: Complete 10-slide outline for your seminar or final project defense.

---

## 🛠️ Technologies Used
- **Language:** Python 3.10+
- **Optimization:** PuLP (COIN-OR CBC Solver), SciPy
- **Data & Analytics:** Pandas, NumPy, Scikit-Learn
- **Visualization:** Plotly Express & Graph Objects, Folium, Streamlit-Folium
- **Web UI:** Streamlit
- **Testing:** Pytest
=======
# supply-chain-optimizer
OptiChain is an interactive Decision Support System (DSS) designed to help businesses optimize transportation, warehouse locations, inventory levels, delivery routes, and demand planning while reducing operational costs.
>>>>>>> 13f45ade0348394492db90761de23fa84e027059
