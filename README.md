# BurnGuard AI — SIH 2026 Demo

**Problem Statement:** SIH26170 — AI-Driven Anomaly Detection in Component Burn-In and Screening  
**Team:** 106

## What is new in this demo

1. Telemetry integrity checks before screening.
2. Dynamic lot-relative baseline using median + MAD / robust z-scores.
3. Early 168h leakage forecasting from 0h + 24h telemetry.
4. Isolation Forest anomaly signal at the latest checkpoint.
5. Physics guardrail using an Arrhenius relative acceleration factor.
6. Bootstrap 90% prediction interval for the early 168h forecast instead of presenting a single forecast as absolute truth.
7. Anomaly fingerprint clustering for pattern discovery.
8. Hash-chained SHA-256 Reliability Passport for tamper-evident screening records.
9. Dataset Explorer with a schema adapter so a compatible burn-in CSV can replace the demo data.
10. Reliability Lab: an interactive what-if stress-temperature sandbox.

## Demo data

The repository includes a clearly labelled **synthetic demo dataset** so the Streamlit app works immediately without a database.

For a public reliability reference, the README points to:
- NASA IGBT accelerated aging data mirrored on Kaggle: https://www.kaggle.com/datasets/vignesh9147/igbt-accelerated-aging-data-set
- Minitab electronic current leakage accelerated-life dataset: https://support.minitab.com/en-us/datasets/reliability-data-sets/electronic-current-leakage/

These public datasets do not have exactly the same 0/24/96/168h multi-signal burn-in schema used by this prototype, so they should not be silently relabelled as if they were the team's actual burn-in dataset.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this folder to a public GitHub repository.
2. Open Streamlit Community Cloud.
3. Select **New app**.
4. Choose the repository and branch.
5. Main file: `app.py`.
6. Deploy.

No database, API key, secret, or paid service is required for the demo.

## Important technical honesty

The Arrhenius module is a **physics-informed guardrail**, not a certified lifetime prediction model. Activation energy is component/material dependent. Before operational use, the physics parameters, limits, uncertainty model, failure signatures and thresholds must be calibrated and validated using approved component qualification/reliability data.

Likewise, anomaly fingerprints are **pattern-discovery labels**, not claims of a specific physical defect mechanism unless engineering evidence validates that mapping.

## Expected CSV schema

`Component_ID, Lot_ID, Time_hr, Leakage_uA, Voltage_V, Current_mA, Prop_Delay_ns, Temperature_C`

`Defect_Label` is optional and is not required for screening logic.
