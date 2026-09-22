import hashlib, json, math, os
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

FEATURES = ["Leakage_uA","Voltage_V","Current_mA","Prop_Delay_ns","Temperature_C"]
TIMES = [0,24,96,168]
LABEL = "Defect_Label"

def load_data(path):
    df = pd.read_csv(path)
    return prepare_data(df)

def prepare_data(df):
    df = df.copy()
    aliases = {
        "component":"Component_ID","component_id":"Component_ID","part_id":"Component_ID",
        "lot":"Lot_ID","lot_id":"Lot_ID","batch":"Lot_ID","batch_id":"Lot_ID",
        "time":"Time_hr","time_hr":"Time_hr","hours":"Time_hr",
        "leakage":"Leakage_uA","leakage_ua":"Leakage_uA","leakage_current":"Leakage_uA",
        "voltage":"Voltage_V","voltage_v":"Voltage_V",
        "current":"Current_mA","current_ma":"Current_mA",
        "prop_delay":"Prop_Delay_ns","propagation_delay":"Prop_Delay_ns","delay":"Prop_Delay_ns",
        "temperature":"Temperature_C","temperature_c":"Temperature_C","temp":"Temperature_C",
        "defect":"Defect_Label","defect_label":"Defect_Label","label":"Defect_Label"
    }
    rename = {}
    normalized = {str(c).strip().lower().replace(" ","_").replace("-","_"): c for c in df.columns}
    for key, target in aliases.items():
        if target not in df.columns and key in normalized:
            rename[normalized[key]] = target
    df = df.rename(columns=rename)
    required = ["Component_ID","Lot_ID","Time_hr"] + FEATURES
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing columns after mapping: " + ", ".join(missing))
    df["Time_hr"] = pd.to_numeric(df["Time_hr"], errors="coerce")
    for c in FEATURES:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Component_ID","Lot_ID","Time_hr"])
    return df

def robust_z_value(x, median, mad):
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale < 1e-9:
        scale = max(float(mad) if np.isfinite(mad) else 0, 1e-6)
    return float((x - median) / scale)

def telemetry_integrity(df):
    out=[]
    for c in FEATURES:
        miss = int(df[c].isna().sum())
        inf = int((~np.isfinite(df[c].fillna(0))).sum())
        out.append({"signal":c,"missing":miss,"non_finite":inf})
    return pd.DataFrame(out)

def lot_evidence(df, component_id, time_hr=168):
    d = df[df["Component_ID"] == component_id].copy()
    if d.empty: return None
    lot = d["Lot_ID"].iloc[0]
    peers = df[(df["Lot_ID"] == lot) & (df["Time_hr"] == time_hr)].copy()
    if peers.empty: peers = df[df["Lot_ID"] == lot].copy()
    row = d.iloc[(d["Time_hr"]-time_hr).abs().argsort()[:1].iloc[0]]
    z={}
    medians={}
    for f in FEATURES:
        vals = peers[f].dropna()
        med = float(vals.median()) if len(vals) else 0
        mad = float((vals-med).abs().median()) if len(vals) else 1
        x = float(row[f]) if pd.notna(row[f]) else med
        z[f] = abs(robust_z_value(x, med, mad))
        medians[f]=med
    return lot, peers, row, z, medians

def fit_isolation_model(df, contamination=0.05):
    latest=df[df["Time_hr"]==168].copy()
    if latest.empty: return None, None
    X=latest[FEATURES].copy().fillna(latest[FEATURES].median())
    scaler=StandardScaler()
    Xs=scaler.fit_transform(X)
    model=IsolationForest(n_estimators=250, contamination=contamination, random_state=42, n_jobs=-1)
    model.fit(Xs)
    latest["IF_score"] = -model.decision_function(Xs)
    return model, scaler, latest

def forecast_168(df, component_id, return_interval=False, n_boot=100):
    wide=df.pivot_table(index=["Component_ID","Lot_ID"],columns="Time_hr",
                        values=FEATURES,aggfunc="mean").reset_index()
    wide.columns=[f"{a}_{int(b)}" if isinstance(a,str) and isinstance(b,(int,np.integer)) else str(a)
                  for a,b in wide.columns]
    needed=["Leakage_uA_0","Leakage_uA_24","Leakage_uA_168"]
    if not all(c in wide.columns for c in needed): return None
    train=wide.dropna(subset=needed).copy()
    if len(train)<20: return None
    X=train[["Leakage_uA_0","Leakage_uA_24"]].to_numpy()
    y=train["Leakage_uA_168"].to_numpy()
    scaler=StandardScaler().fit(X)
    model=Ridge(alpha=1.0).fit(scaler.transform(X), y)

    x=df[df["Component_ID"]==component_id].pivot_table(index="Component_ID",columns="Time_hr",
                                                        values="Leakage_uA",aggfunc="mean")
    if component_id not in x.index or not {0,24}.issubset(x.columns): return None
    vals=x.loc[component_id,[0,24]].astype(float)
    vals=vals.fillna(pd.Series({0:train["Leakage_uA_0"].median(),24:train["Leakage_uA_24"].median()}))
    xnew=np.array([[float(vals.iloc[0]),float(vals.iloc[1])]])
    pred=float(model.predict(scaler.transform(xnew))[0])

    if not return_interval:
        return pred

    rng=np.random.default_rng(42)
    preds=[]
    for _ in range(n_boot):
        idx=rng.integers(0,len(train),len(train))
        xb=X[idx]; yb=y[idx]
        sc=StandardScaler().fit(xb)
        m=Ridge(alpha=1.0).fit(sc.transform(xb),yb)
        preds.append(float(m.predict(sc.transform(xnew))[0]))
    lo,hi=np.percentile(preds,[5,95])
    return {"prediction":pred,"low":float(lo),"high":float(hi)}

def arrhenius_factor(temp_c, ref_c=25.0, ea_ev=0.70):
    # Relative acceleration factor. This is a physics guardrail, not a calibrated lifetime model.
    k=8.617333262e-5
    T=max(float(temp_c)+273.15, 1)
    R=max(float(ref_c)+273.15, 1)
    return float(np.exp((ea_ev/k)*(1/R - 1/T)))

def physics_guardrail(df, component_id):
    d=df[df["Component_ID"]==component_id].sort_values("Time_hr")
    if d.empty: return {"factor":1.0,"status":"No data","score":0.0}
    t=float(d["Temperature_C"].mean())
    af=arrhenius_factor(t)
    # Normalize only for a dashboard indicator.
    score=float(np.clip((np.log1p(af)/5)*100,0,100))
    return {"factor":af,"status":"Physics consistency indicator","score":score,"mean_temp":t}

def bootstrap_confidence(df, component_id, n=80):
    d=df[df["Component_ID"]==component_id].sort_values("Time_hr")
    if d.empty: return None
    y=d["Leakage_uA"].dropna().to_numpy()
    if len(y)<3: return None
    rng=np.random.default_rng(42)
    means=[float(np.mean(rng.choice(y,size=len(y),replace=True))) for _ in range(n)]
    lo,hi=np.percentile(means,[5,95])
    return {"center":float(np.mean(y)),"low":float(lo),"high":float(hi)}

def fingerprint(df, component_id):
    ev=lot_evidence(df,component_id)
    if ev is None:return {"label":"Unknown","profile":{}}
    _,_,_,z,_=ev
    ranked=sorted(z.items(), key=lambda x:x[1], reverse=True)
    top=dict(ranked[:2])
    if "Leakage_uA" in top and "Current_mA" in top: label="Electrical leakage-current"
    elif "Temperature_C" in top and "Leakage_uA" in top: label="Thermal-electrical"
    elif "Prop_Delay_ns" in top: label="Timing-dominant"
    else: label="Multivariate deviation"
    return {"label":label,"profile":z}

def risk_record(df, component_id):
    ev=lot_evidence(df,component_id)
    if ev is None:return None
    lot,peers,row,z,medians=ev
    mean_z=float(np.mean(list(z.values())))
    anomaly_score=float(np.clip(mean_z/8,0,1)*100)

    # Independent multivariate anomaly evidence from Isolation Forest.
    _, _, latest_if = fit_isolation_model(df)
    if_score=0.0
    if latest_if is not None:
        hit=latest_if[latest_if["Component_ID"]==component_id]
        if not hit.empty:
            # decision_function: negative is more anomalous; map to a stable demo score.
            if_score=float(np.clip((float(hit["IF_score"].iloc[0])+0.5),0,1)*100)

    pred_info=forecast_168(df,component_id,return_interval=True)
    pred=pred_info["prediction"] if isinstance(pred_info,dict) else pred_info
    actual=float(row["Leakage_uA"]) if pd.notna(row["Leakage_uA"]) else medians["Leakage_uA"]
    residual=float(actual-pred) if pred is not None else 0.0
    prediction_risk=float(np.clip(abs(residual)/8,0,1)*100)
    phys=physics_guardrail(df,component_id)
    # Physics is a guardrail signal, not a direct replacement for empirical screening.
    physics_risk=float(np.clip(phys["score"]/100,0,1)*100)
    risk=float(np.clip(0.45*anomaly_score+0.15*if_score+0.25*prediction_risk+0.15*physics_risk,0,100))
    verdict="Reject" if risk>=70 else ("Monitor" if risk>=40 else "Pass")
    total=sum(z.values()) or 1
    contrib=[{"channel":f,"z_score":round(z[f],2),"contribution_pct":round(100*z[f]/total,1)} for f in FEATURES]
    contrib.sort(key=lambda x:x["contribution_pct"],reverse=True)
    conf=bootstrap_confidence(df,component_id)
    fp=fingerprint(df,component_id)
    return {"component_id":component_id,"lot_id":lot,"risk_score":round(risk,1),"verdict":verdict,
            "actual_168":actual,"predicted_168":pred,"residual":residual,"zvals":z,
            "contributions":contrib,"lot_medians":medians,"lot_size":len(peers),
            "isolation_forest_score":if_score,"physics":phys,"confidence":conf,
            "forecast_interval": pred_info if isinstance(pred_info,dict) else None,
            "fingerprint":fp,"history":df[df["Component_ID"]==component_id].sort_values("Time_hr")}

def score_all(df):
    rows=[]
    for cid in df["Component_ID"].dropna().unique():
        r=risk_record(df,cid)
        if r: rows.append({"Component_ID":cid,"Lot_ID":r["lot_id"],"Risk_Score":r["risk_score"],
                           "Verdict":r["verdict"],"Leakage_168":r["actual_168"],
                           "Predicted_168":r["predicted_168"],"Residual":r["residual"],
                           "Top_Reason":r["contributions"][0]["channel"],
                           "Fingerprint":r["fingerprint"]["label"]})
    return pd.DataFrame(rows)

def cluster_fingerprints(df, scores):
    if scores.empty:return pd.DataFrame()
    rows=[]
    for cid in scores["Component_ID"].head(250):
        r=risk_record(df,cid)
        rows.append([cid]+[r["zvals"][f] for f in FEATURES])
    X=np.array([x[1:] for x in rows])
    k=min(4,max(2,len(rows)//30))
    km=KMeans(n_clusters=k,random_state=42,n_init=10).fit(X)
    out=pd.DataFrame(rows,columns=["Component_ID"]+FEATURES)
    out["Cluster"]=km.labels_+1
    return out

def append_audit(path, record):
    os.makedirs(os.path.dirname(path),exist_ok=True)
    prev=""
    if os.path.exists(path):
        with open(path,"rb") as f: prev=hashlib.sha256(f.read()).hexdigest()
    payload={"timestamp":datetime.now(timezone.utc).isoformat(),"previous_hash":prev,**record}
    raw=json.dumps(payload,sort_keys=True).encode()
    payload["record_hash"]=hashlib.sha256(raw).hexdigest()
    with open(path,"a",encoding="utf-8") as f: f.write(json.dumps(payload)+"\n")
    return payload