import streamlit as st
import plotly.graph_objects as go
from common import setup,get_demo_data,scores_for
from model import risk_record,arrhenius_factor

setup("BurnGuard AI — Reliability Lab")
df=get_demo_data(); scores=scores_for(df)
cid=st.selectbox("Component for what-if analysis",scores.sort_values("Risk_Score",ascending=False).Component_ID.head(100))
rec=risk_record(df,cid)

st.title("Reliability Lab")
st.caption("Interactive stress-test sandbox — demonstrate how BurnGuard can connect statistical evidence with reliability physics.")

temp=st.slider("Hypothetical stress temperature (°C)",40,140,85)
ea=st.slider("Activation energy assumption (eV)",0.3,1.2,0.70,0.05)
ref=25.0
factor=arrhenius_factor(temp,ref,ea)

c1,c2,c3=st.columns(3)
c1.metric("Arrhenius acceleration factor",f"{factor:,.1f}×")
c2.metric("Reference temperature",f"{ref:.0f} °C")
c3.metric("Activation energy assumption",f"{ea:.2f} eV")

st.markdown("### Physics cross-check")
st.info("The Arrhenius relationship is shown here as a relative acceleration factor. It is a guardrail/consistency signal, not a claim that one universal activation energy predicts every component family.")

temps=list(range(40,141,5))
factors=[arrhenius_factor(t,ref,ea) for t in temps]
fig=go.Figure(go.Scatter(x=temps,y=factors,mode="lines+markers"))
fig.add_vline(x=temp,line_dash="dash")
fig.update_layout(height=400,xaxis_title="Stress temperature (°C)",yaxis_title="Relative acceleration factor")
st.plotly_chart(fig,use_container_width=True)

st.markdown("### The panel-ready idea")
st.write("If the ML forecast and the physics-informed expectation strongly disagree, BurnGuard does not hide the disagreement. It surfaces it for engineering review. This is a safer design than treating a statistical model as an unquestionable oracle.")