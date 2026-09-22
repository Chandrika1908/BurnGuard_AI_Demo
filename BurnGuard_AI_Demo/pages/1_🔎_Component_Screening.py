import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from common import setup,get_demo_data,scores_for,chip
from model import risk_record

setup("BurnGuard AI — Component Screening")
df=get_demo_data(); scores=scores_for(df)
ids=scores.sort_values("Risk_Score",ascending=False).Component_ID.tolist()
cid=st.selectbox("Select component",ids,format_func=lambda x:f"{x} · Lot {df.loc[df.Component_ID==x,'Lot_ID'].iloc[0]}")
rec=risk_record(df,cid)

st.markdown(f'<div class="card"><span class="muted">QA DECISION</span><h2>{cid}</h2>{chip(rec["verdict"])} &nbsp; Lot {rec["lot_id"]} · {rec["lot_size"]} peers</div>',unsafe_allow_html=True)
a,b,c,d=st.columns(4)
a.metric("Risk score",f'{rec["risk_score"]:.0f}/100')
b.metric("168h leakage",f'{rec["actual_168"]:.2f} µA')
c.metric("Early forecast",f'{rec["predicted_168"]:.2f} µA' if rec["predicted_168"] is not None else "N/A")
d.metric("Forecast residual",f'{rec["residual"]:+.2f} µA')

st.markdown('<div class="section">Telemetry vs lot behaviour</div>',unsafe_allow_html=True)
hist=rec["history"]; peers=df[(df.Lot_ID==rec["lot_id"])]
band=peers.groupby("Time_hr").Leakage_uA.agg(["median","std"]).reset_index()
fig=go.Figure()
upper=band["median"]+2*band["std"].fillna(0); lower=band["median"]-2*band["std"].fillna(0)
fig.add_trace(go.Scatter(x=band.Time_hr,y=upper,mode="lines",line=dict(width=0),showlegend=False))
fig.add_trace(go.Scatter(x=band.Time_hr,y=lower,mode="lines",fill="tonexty",fillcolor="rgba(37,99,235,.10)",line=dict(width=0),name="Lot ±2σ band"))
fig.add_trace(go.Scatter(x=band.Time_hr,y=band["median"],mode="lines+markers",name="Lot median",line=dict(width=3)))
fig.add_trace(go.Scatter(x=hist.Time_hr,y=hist.Leakage_uA,mode="lines+markers",name=cid,line=dict(width=4)))
if rec["predicted_168"] is not None and (hist.Time_hr==24).any():
    y24=float(hist.loc[hist.Time_hr==24,"Leakage_uA"].iloc[0])
    fig.add_trace(go.Scatter(x=[24,168],y=[y24,rec["predicted_168"]],mode="lines+markers",name="ML early forecast",line=dict(dash="dash",width=3)))
fig.update_layout(height=450,xaxis_title="Burn-in checkpoint (h)",yaxis_title="Leakage (µA)",margin=dict(l=10,r=10,t=10,b=10))
st.plotly_chart(fig,use_container_width=True)

l,r=st.columns([1.2,1])
with l:
    st.markdown('<div class="section">Evidence channels</div>',unsafe_allow_html=True)
    contrib=pd.DataFrame(rec["contributions"])
    fig2=px.bar(contrib.sort_values("z_score"),x="z_score",y="channel",orientation="h",text="z_score")
    fig2.update_layout(height=340,xaxis_title="Absolute robust z-score",yaxis_title="")
    fig2.update_traces(textposition="outside")
    st.plotly_chart(fig2,use_container_width=True)
with r:
    st.markdown('<div class="section">Why was it flagged?</div>',unsafe_allow_html=True)
    st.write(f'**Primary fingerprint:** {rec["fingerprint"]["label"]}')
    st.write(f'**Top signal:** {rec["contributions"][0]["channel"]} ({rec["contributions"][0]["contribution_pct"]:.1f}% of lot-relative evidence)')
    st.write(f'**Mean lot anomaly A:** {np.mean(list(rec["zvals"].values())):.2f}' if False else f'**Mean lot anomaly A:** {sum(rec["zvals"].values())/len(rec["zvals"]):.2f}')
    st.write(f'**Prediction risk P:** {abs(rec["residual"])/8*100:.1f}/100')
    st.write(f'**Isolation Forest anomaly:** {rec["isolation_forest_score"]:.1f}/100')
    st.write(f'**Physics indicator:** {rec["physics"]["score"]:.1f}/100')
    if rec["forecast_interval"]:
        fi=rec["forecast_interval"]
        st.write(f'**Bootstrap 90% forecast interval:** {fi["low"]:.2f}–{fi["high"]:.2f} µA')
    if rec["confidence"]:
        st.write(f'**Bootstrap uncertainty:** mean {rec["confidence"]["center"]:.2f} µA; 90% interval {rec["confidence"]["low"]:.2f}–{rec["confidence"]["high"]:.2f} µA')

st.markdown('<div class="section">Raw telemetry</div>',unsafe_allow_html=True)
st.dataframe(hist[["Time_hr"]+["Leakage_uA","Voltage_V","Current_mA","Prop_Delay_ns","Temperature_C"]],use_container_width=True,hide_index=True)