import streamlit as st
import plotly.express as px
from common import setup,get_demo_data,scores_for

setup("BurnGuard AI — Command Center")
df=get_demo_data(); scores=scores_for(df)

st.markdown("""
<div class="hero">
<div class="eyebrow">SIH 2026 · SIH26170 · SMART AUTOMATION</div>
<h1>BurnGuard AI</h1>
<p>From raw burn-in telemetry to a defensible reliability decision — combining lot-relative anomaly detection, early drift prediction, a physics guardrail, uncertainty, anomaly fingerprints and a tamper-evident audit trail.</p>
</div>
""",unsafe_allow_html=True)

c1,c2,c3,c4=st.columns(4)
for c,label,val,note in [
    (c1,"Components screened",len(scores),"live demo population"),
    (c2,"High-risk",int((scores.Risk_Score>=70).sum()),"requires QA review"),
    (c3,"Monitor",int(((scores.Risk_Score>=40)&(scores.Risk_Score<70)).sum()),"early warning"),
    (c4,"Lots analysed",df.Lot_ID.nunique(),"peer populations")]:
    c.metric(label,val,note)

st.markdown('<div class="section">The BurnGuard intelligence loop</div>',unsafe_allow_html=True)
cols=st.columns(6)
steps=[("01","Integrity","Trust the telemetry"),("02","Baseline","Compare with its lot"),("03","Predict","Estimate 168h behaviour"),
       ("04","Guardrail","Check physics consistency"),("05","Fingerprint","Identify the anomaly pattern"),("06","Passport","Record the evidence")]
for c,(n,t,d) in zip(cols,steps):
    with c:
        st.markdown(f'<div class="card"><b>{n} · {t}</b><div class="muted" style="margin-top:8px">{d}</div></div>',unsafe_allow_html=True)

st.markdown('<div class="section">⚡ Demo wow factor: Physics–AI disagreement</div>',unsafe_allow_html=True)
w1,w2,w3=st.columns(3)
with w1:
    st.markdown('<div class="wow"><h3>AI says</h3><p>“This component is deviating from its lot and its early leakage trend predicts elevated 168h behaviour.”</p></div>',unsafe_allow_html=True)
with w2:
    st.markdown('<div class="wow"><h3>Physics asks</h3><p>“Is the observed thermal environment consistent with the amount of accelerated aging implied by the signal?”</p></div>',unsafe_allow_html=True)
with w3:
    st.markdown('<div class="wow"><h3>BurnGuard decides</h3><p>“Show the evidence, quantify uncertainty, and route the part for the appropriate QA action.”</p></div>',unsafe_allow_html=True)

st.markdown('<div class="section">Top-risk queue</div>',unsafe_allow_html=True)
top=scores.sort_values("Risk_Score",ascending=False).head(15)
fig=px.bar(top.sort_values("Risk_Score"),x="Risk_Score",y="Component_ID",color="Verdict",orientation="h",text="Risk_Score")
fig.update_layout(height=500,margin=dict(l=5,r=15,t=5,b=5),xaxis_title="Risk / 100",yaxis_title="")
fig.update_traces(textposition="outside")
st.plotly_chart(fig,use_container_width=True)

st.info("This is a research/demo prototype. The Arrhenius module is used as a physics-consistency guardrail; it is not presented as a certified component lifetime model. Real deployment would require calibration against the component family, qualification data and approved reliability procedures.")