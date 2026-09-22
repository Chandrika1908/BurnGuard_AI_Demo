import streamlit as st, os, json, hashlib
from common import setup,get_demo_data,scores_for
from model import risk_record,append_audit
from common import AUDIT_PATH

setup("BurnGuard AI — Reliability Passport")
df=get_demo_data(); scores=scores_for(df)
st.title("Reliability Passport")
st.caption("A hash-chained audit trail for screening decisions — designed to make the demo decision traceable and tamper-evident.")

cid=st.selectbox("Select decision to record",scores.sort_values("Risk_Score",ascending=False).Component_ID.head(100))
if st.button("Record screening decision",type="primary"):
    r=risk_record(df,cid)
    payload={"component_id":cid,"lot_id":r["lot_id"],"risk_score":r["risk_score"],"verdict":r["verdict"],
             "top_signal":r["contributions"][0]["channel"],"model_version":"BurnGuard-demo-v1"}
    rec=append_audit(AUDIT_PATH,payload)
    st.success(f"Recorded. Hash: {rec['record_hash'][:16]}…")

if os.path.exists(AUDIT_PATH):
    lines=open(AUDIT_PATH,encoding="utf-8").read().splitlines()
    records=[json.loads(x) for x in lines[-20:]]
    st.markdown("### Recent records")
    st.dataframe(records,use_container_width=True)
    st.info("Each record stores the previous record hash and its own SHA-256 hash. This makes later edits detectable; it is not the same as a blockchain and should be backed by controlled storage in a production system.")
else:
    st.info("No decisions recorded yet. Use the button above to create the first passport entry.")