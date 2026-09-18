"""YUKTHI — Intelligent Chiller Energy & Equipment Monitoring Dashboard.

Streamlit dashboard for chronological replay of chiller monitoring data.
Shows actual vs expected energy, residual analysis, anomaly events,
and SHAP explanations.
"""
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from catboost import CatBoostRegressor

# Add project root to path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.anomaly import AnomalyEvent, score_anomalies
from src.constants import (
    COL_ANOMALY_FLAG,
    COL_BUILDING_LOAD,
    COL_CHILLED_WATER_RATE,
    COL_COOLING_WATER_TEMP,
    COL_ENERGY,
    COL_EQUIPMENT_ID,
    COL_EVENT_ID,
    COL_EXPECTED_ENERGY,
    COL_HUMIDITY,
    COL_OUTSIDE_TEMP,
    COL_RESIDUAL,
    COL_TIMESTAMP,
    COL_Z_SCORE,
    FEATURE_COLS,
)
from src.data_loader import load_and_validate
from src.explain import explain_prediction, generate_narrative
from src.features import engineer_features
from src.predict import predict_expected_energy
from src.preprocessing import preprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="YUKTHI — Chiller Intelligence",
    page_icon="⚡",
    layout="wide",
)


@st.cache_data
def load_pipeline_data(csv_path: str) -> pd.DataFrame:
    """Load, preprocess, and engineer features for the dataset."""
    df = load_and_validate(Path(csv_path))
    df, _gap_report = preprocess(df)
    df = engineer_features(df)
    return df


@st.cache_resource
def load_trained_model(model_path: str) -> CatBoostRegressor:
    """Load a trained CatBoost model from disk."""
    model = CatBoostRegressor()
    model.load_model(model_path)
    return model


def _render_header() -> None:
    """Render the dashboard header."""
    st.title("⚡ YUKTHI — Intelligent Chiller Monitoring")
    st.markdown(
        "Contextual expected-behaviour modelling for chiller energy. "
        "**Detect. Understand. Assess. Act.**"
    )


def _render_sidebar(
    df: pd.DataFrame,
) -> tuple[str, pd.Timestamp, pd.Timestamp]:
    """Render sidebar controls and return selections."""
    st.sidebar.header("🎛️ Controls")

    equipment_ids = sorted(df[COL_EQUIPMENT_ID].unique().tolist())
    selected_equip = st.sidebar.selectbox(
        "Equipment", equipment_ids,
    )

    equip_data = df[df[COL_EQUIPMENT_ID] == selected_equip]
    min_date = equip_data[COL_TIMESTAMP].min().date()
    max_date = equip_data[COL_TIMESTAMP].max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date = pd.Timestamp(date_range[0])
        end_date = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
    else:
        start_date = pd.Timestamp(min_date)
        end_date = pd.Timestamp(max_date) + pd.Timedelta(days=1)

    return str(selected_equip), start_date, end_date


def _render_kpi_cards(filtered: pd.DataFrame) -> None:
    """Render top-level KPI metric cards."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Observations", f"{len(filtered):,}",
        )
    with col2:
        mean_actual = filtered[COL_ENERGY].mean()
        st.metric("Avg Actual (kWh)", f"{mean_actual:.1f}")
    with col3:
        mean_expected = filtered[COL_EXPECTED_ENERGY].mean()
        st.metric("Avg Expected (kWh)", f"{mean_expected:.1f}")
    with col4:
        mean_residual = filtered[COL_RESIDUAL].mean()
        st.metric("Avg Deviation (kWh)", f"{mean_residual:+.1f}")
    with col5:
        anomaly_pct = (
            filtered[COL_ANOMALY_FLAG].sum() / max(len(filtered), 1) * 100
        )
        st.metric("Anomaly Rate", f"{anomaly_pct:.1f}%")


def _render_energy_chart(filtered: pd.DataFrame) -> None:
    """Render actual vs expected energy time series."""
    st.subheader("📈 Actual vs Expected Energy")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=filtered[COL_TIMESTAMP],
        y=filtered[COL_ENERGY],
        name="Actual Energy",
        mode="lines",
        line={"color": "#e74c3c", "width": 1.5},
    ))
    fig.add_trace(go.Scatter(
        x=filtered[COL_TIMESTAMP],
        y=filtered[COL_EXPECTED_ENERGY],
        name="Expected Energy",
        mode="lines",
        line={"color": "#3498db", "width": 1.5, "dash": "dash"},
    ))

    # Highlight anomaly regions
    anomaly_rows = filtered[filtered[COL_ANOMALY_FLAG] == 1]
    if not anomaly_rows.empty:
        fig.add_trace(go.Scatter(
            x=anomaly_rows[COL_TIMESTAMP],
            y=anomaly_rows[COL_ENERGY],
            name="Anomaly",
            mode="markers",
            marker={"color": "#e67e22", "size": 6, "symbol": "x"},
        ))

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Energy (kWh)",
        height=400,
        legend={"orientation": "h", "y": 1.1},
        margin={"l": 40, "r": 20, "t": 20, "b": 40},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_residual_chart(filtered: pd.DataFrame) -> None:
    """Render residual plot with anomaly zones."""
    st.subheader("📊 Residual Analysis")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=filtered[COL_TIMESTAMP],
        y=filtered[COL_RESIDUAL],
        name="Residual (kWh)",
        marker_color=np.where(
            filtered[COL_ANOMALY_FLAG] == 1, "#e67e22", "#95a5a6",
        ),
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="#2c3e50")
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Residual (kWh)",
        height=300,
        margin={"l": 40, "r": 20, "t": 20, "b": 40},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_observation_detail(
    row: pd.Series,
    model: CatBoostRegressor,
    df_row: pd.DataFrame,
) -> None:
    """Render detail panel for a selected observation."""
    st.subheader("🔍 Observation Detail")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Reading**")
        st.markdown(f"- **Actual Energy:** {row[COL_ENERGY]:.1f} kWh")
        st.markdown(
            f"- **Expected Energy:** {row[COL_EXPECTED_ENERGY]:.1f} kWh"
        )
        st.markdown(f"- **Deviation:** {row[COL_RESIDUAL]:+.1f} kWh")

        status = "⚠️ INVESTIGATE" if row[COL_ANOMALY_FLAG] == 1 else "✅ NORMAL"
        st.markdown(f"- **Status:** {status}")

    with col2:
        st.markdown("**Operating Context**")
        st.markdown(
            f"- Building Load: {row.get(COL_BUILDING_LOAD, 'N/A'):.1f} RT"
        )
        st.markdown(
            f"- Cooling Water: "
            f"{row.get(COL_COOLING_WATER_TEMP, 'N/A'):.1f} °C"
        )
        st.markdown(
            f"- Flow Rate: "
            f"{row.get(COL_CHILLED_WATER_RATE, 'N/A'):.1f} L/s"
        )
        st.markdown(
            f"- Outside Temp: {row.get(COL_OUTSIDE_TEMP, 'N/A'):.1f} °F"
        )

    # SHAP explanation
    try:
        explanation = explain_prediction(model, df_row, FEATURE_COLS)
        narrative = generate_narrative(explanation)
        st.markdown("**📝 Model Explanation**")
        st.info(narrative)

        # SHAP bar chart
        top = explanation.top_contributors
        shap_df = pd.DataFrame([
            {"Feature": c.feature_name, "SHAP Value (kWh)": c.shap_value}
            for c in top
        ])
        fig = px.bar(
            shap_df, x="SHAP Value (kWh)", y="Feature",
            orientation="h",
            color="SHAP Value (kWh)",
            color_continuous_scale=["#3498db", "#95a5a6", "#e74c3c"],
        )
        fig.update_layout(
            height=250,
            margin={"l": 20, "r": 20, "t": 10, "b": 20},
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.warning(f"SHAP explanation unavailable: {exc}")


def _render_event_log(events: list[AnomalyEvent]) -> None:
    """Render the anomaly event log table."""
    st.subheader("📋 Anomaly Event Log")

    if not events:
        st.success("No anomaly events detected in this range.")
        return

    event_data = [
        {
            "Event": e.event_id,
            "Equipment": e.equipment_id,
            "Start": e.start_time,
            "End": e.end_time,
            "Duration (min)": e.duration_minutes,
            "Max Deviation (kWh)": f"{e.max_residual:+.1f}",
            "Mean Deviation (kWh)": f"{e.mean_residual:+.1f}",
            "Observations": e.observation_count,
        }
        for e in events
    ]
    st.dataframe(pd.DataFrame(event_data), use_container_width=True)


def main() -> None:
    """Main dashboard entry point."""
    _render_header()

    # ── Paths ───────────────────────────────────────────────────
    csv_path = str(_PROJECT_ROOT / "data" / "raw" / "chiller_data.csv")
    model_path = str(_PROJECT_ROOT / "models" / "catboost_expected_energy.cbm")

    model_exists = Path(model_path).exists()

    if not model_exists:
        st.warning(
            "⚠️ No trained model found at `models/catboost_expected_energy.cbm`. "
            "Run training first: `python -m src.train`"
        )
        st.stop()

    # ── Load data and model ─────────────────────────────────────
    with st.spinner("Loading data and model..."):
        df = load_pipeline_data(csv_path)
        model = load_trained_model(model_path)
        df = predict_expected_energy(model, df, FEATURE_COLS)
        df, events = score_anomalies(df)

    # ── Sidebar controls ────────────────────────────────────────
    selected_equip, start_date, end_date = _render_sidebar(df)

    filtered = df[
        (df[COL_EQUIPMENT_ID] == selected_equip)
        & (df[COL_TIMESTAMP] >= start_date)
        & (df[COL_TIMESTAMP] < end_date)
    ].sort_values(COL_TIMESTAMP)

    filtered_events = [
        e for e in events
        if e.equipment_id == selected_equip
        and e.start_time >= start_date
        and e.end_time < end_date
    ]

    if filtered.empty:
        st.warning("No data for the selected equipment and date range.")
        st.stop()

    # ── KPIs ────────────────────────────────────────────────────
    _render_kpi_cards(filtered)

    # ── Charts ──────────────────────────────────────────────────
    _render_energy_chart(filtered)
    _render_residual_chart(filtered)

    # ── Observation selector ────────────────────────────────────
    st.subheader("🔎 Inspect Observation")
    obs_idx = st.slider(
        "Select observation",
        min_value=0,
        max_value=len(filtered) - 1,
        value=0,
    )
    selected_row = filtered.iloc[obs_idx]
    selected_df = filtered.iloc[[obs_idx]]
    _render_observation_detail(selected_row, model, selected_df)

    # ── Event log ───────────────────────────────────────────────
    _render_event_log(filtered_events)

    # ── Sidebar model metrics ───────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Model Info**")
    st.sidebar.markdown(f"- Features: {len(FEATURE_COLS)}")
    st.sidebar.markdown(f"- Total observations: {len(df):,}")
    st.sidebar.markdown(
        f"- Equipment: {len(df[COL_EQUIPMENT_ID].unique())}"
    )


if __name__ == "__main__":
    main()
