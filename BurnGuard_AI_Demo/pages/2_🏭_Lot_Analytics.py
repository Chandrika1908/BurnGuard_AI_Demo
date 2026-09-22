import streamlit as st
import plotly.express as px
from common import setup,get_demo_data,scores_for
from model import cluster_fingerprints

setup("BurnGuard AI — Lot Analytics")
df=get_demo_data(); scores=scores_for(df)
st.title("Manufacturing Lot Intelligence")
st.caption("Move from individual screening to batch-level quality signals.")

summary=scores.groupby("Lot_ID").agg(Components=("Component_ID","nunique"),Avg_Risk=("Risk_Score","mean"),Max_Risk=("Risk_Score","max"),High_Risk=("Risk_Score",lambda x:int((x>=70).sum()))).reset_index().sort_values("Avg_Risk",ascending=False)
fig=px.bar(summary,x="Lot_ID",y="Avg_Risk",text=summary.Avg_Risk.round(0),hover_data=["Components","Max_Risk","High_Risk"])
fig.update_layout(height=380,xaxis_title="Lot",yaxis_title="Average risk")
st.plotly_chart(fig,use_container_width=True)

st.markdown("### Anomaly fingerprint clusters")
clusters=cluster_fingerprints(df,scores)
if not clusters.empty:
    st.dataframe(clusters.groupby("Cluster")[["Leakage_uA","Voltage_V","Current_mA","Prop_Delay_ns","Temperature_C"]].mean().round(2),use_container_width=True)
    st.caption("Clusters are pattern-discovery aids, not certified physical failure-mode diagnoses. Engineering qualification data is required before naming a root cause.")