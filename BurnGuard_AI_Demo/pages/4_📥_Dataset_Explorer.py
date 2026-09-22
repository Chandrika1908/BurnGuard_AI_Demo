import streamlit as st
import pandas as pd
from common import setup,get_demo_data,scores_for
from model import prepare_data,telemetry_integrity

setup("BurnGuard AI — Dataset Explorer")
demo=get_demo_data()
st.title("Dataset Explorer")
st.caption("BurnGuard is designed around a schema adapter so the demo can be replaced by another burn-in/reliability telemetry CSV.")

uploaded=st.file_uploader("Upload compatible CSV",type=["csv"])
df=demo if uploaded is None else prepare_data(pd.read_csv(uploaded))

st.write(f"Rows: **{len(df):,}** · Components: **{df.Component_ID.nunique():,}** · Lots: **{df.Lot_ID.nunique():,}**")
st.markdown("### Telemetry integrity")
st.dataframe(telemetry_integrity(df),use_container_width=True,hide_index=True)
st.markdown("### Expected schema")
st.code("Component_ID, Lot_ID, Time_hr, Leakage_uA, Voltage_V, Current_mA, Prop_Delay_ns, Temperature_C")
st.dataframe(df.head(20),use_container_width=True,hide_index=True)