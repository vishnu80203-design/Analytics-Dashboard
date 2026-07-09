import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="IIoT Fleet Analytics", layout="wide")
st.title("Defense Manufacturing: Fleet OEE Dashboard")
st.markdown("Real-time telemetry and Overall Equipment Effectiveness (OEE) across 50 assets.")

@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_parquet('fleet_iiot_metrics.parquet')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values(by='timestamp')
    except FileNotFoundError:
        st.error("CRITICAL ERROR: 'fleet_iiot_metrics.parquet' not found.")
        st.stop()

df = load_data()

# SIDEBAR: Fleet Orchestration
st.sidebar.header("Asset Controls")
machine_list = sorted(df['machine_id'].unique().tolist())
selected_machine = st.sidebar.selectbox("Select Machining Asset", ["Fleet Overview"] + machine_list)

# LOGIC: Filter for single machine OR average out the fleet
if selected_machine != "Fleet Overview":
    display_df = df[df['machine_id'] == selected_machine].copy()
    st.subheader(f"Asset Performance: {selected_machine}")
else:
    display_df = df.groupby('timestamp').mean(numeric_only=True).reset_index()
    st.subheader("Fleet-Wide Average Performance")

# EXECUTIVE KPI ROW
latest_data = display_df.iloc[-1]

col1, col2, col3, col4 = st.columns(4)
col1.metric("OEE Score", f"{latest_data['OEE_Score'] * 100:.1f}%")
col2.metric("Availability", f"{latest_data['Availability'] * 100:.1f}%", f"-{latest_data.get('FAILURE', 0):.1f} mins downtime", delta_color="inverse")
col3.metric("Performance", f"{latest_data['Performance'] * 100:.1f}%")
col4.metric("Quality", f"{latest_data['Quality'] * 100:.1f}%", f"{latest_data.get('defective_parts', 0):.1f} avg defects", delta_color="inverse")

st.divider()

# TIME-SERIES VISUALIZATIONS
st.subheader("Operational Trends")

fig_oee = px.line(display_df, x='timestamp', y=['OEE_Score', 'Availability', 'Performance', 'Quality'], 
                  title="OEE Degradation Curve",
                  labels={'value': 'Percentage', 'variable': 'Metric'},
                  color_discrete_sequence=['#FFFFFF', '#00E676', '#29B6F6', '#FFA726'])
fig_oee.layout.yaxis.tickformat = ',.0%'
st.plotly_chart(fig_oee, use_container_width=True)

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    fig_stress = px.scatter(display_df, x='vibration_level', y='temperature', size='power_consumption', 
                            color='FAILURE', title="Mechanical Stress vs. Failure Time (Color = Minutes Lost)",
                            color_continuous_scale="Reds")
    st.plotly_chart(fig_stress, use_container_width=True)

with col_chart2:
    fig_production = px.area(display_df, x='timestamp', y=['produced_parts', 'defective_parts'], 
                             title="Throughput vs. Defect Rate",
                             color_discrete_sequence=['#29B6F6', '#E53935'])
    st.plotly_chart(fig_production, use_container_width=True)
