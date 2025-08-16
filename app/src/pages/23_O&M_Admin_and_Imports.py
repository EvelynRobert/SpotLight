# 23_O&M_Admin_and_Imports.py
import json
import io
from datetime import date
import pandas as pd
import requests
import streamlit as st

# --- Page setup (call before anything renders) ---
st.set_page_config(page_title="O&M Admin & Imports", page_icon="🛠️", layout="wide")
st.title("🛠️ O&M — Admin & Imports")
# --- import sidebar helper no matter where nav.py lives ---
try:
    from modules.nav import SideBarLinks  # your repo variant
except ModuleNotFoundError:
    try:
        from nav import SideBarLinks  # alt location
    except ModuleNotFoundError:
        # tiny fallback so page still works
        def SideBarLinks():
            with st.sidebar:
                st.page_link("Home.py", label="🏠 Home")
                st.subheader("O&M")
                st.page_link("pages/20_dashboard.py", label="O&M Dashboard")
                st.page_link("pages/21_statistics.py", label="Statistics")
                st.page_link("pages/22_management_map.py", label="Management Map")
                st.page_link("pages/23_O&M_Admin_and_Imports.py", label="Admin & Imports")
                st.divider()
                if st.button("🚪 Log out", use_container_width=True):
                    for k in ("persona","cID","active_order_id","map_lat","map_lng","role","authenticated"):
                        st.session_state.pop(k, None)
                    st.switch_page("Home.py")


# --- API bases (adjust if your docker/ports differ) ---
API_OAM = "http://web-api:4000/o_and_m"
API_SALESMAN = "http://web-api:4000/salesman"

# --- HTTP helpers with safe JSON handling ---
def _json_or_text(r):
    ctype = r.headers.get("content-type", "")
    if "application/json" in ctype:
        try:
            return r.json()
        except Exception:
            return {"error": "Invalid JSON in response"}
    return r.text

def get_json(url, **kw):
    try:
        r = requests.get(url, timeout=30, **kw)
        return r.status_code, _json_or_text(r)
    except Exception as e:
        return 0, {"error": str(e)}

def post_json(url, payload=None, **kw):
    try:
        r = requests.post(url, json=payload, timeout=30, **kw)
        return r.status_code, _json_or_text(r)
    except Exception as e:
        return 0, {"error": str(e)}

def put_json(url, payload=None, **kw):
    try:
        r = requests.put(url, json=payload, timeout=30, **kw)
        return r.status_code, _json_or_text(r)
    except Exception as e:
        return 0, {"error": str(e)}

def delete_json(url, **kw):
    try:
        r = requests.delete(url, timeout=30, **kw)
        return r.status_code, _json_or_text(r)
    except Exception as e:
        return 0, {"error": str(e)}

# Utility: try a list of endpoints and return the first 200
def try_endpoints(method, endpoints_with_payload):
    for url, payload in endpoints_with_payload:
        if method == "GET":
            code, data = get_json(url)
        elif method == "POST":
            code, data = post_json(url, payload)
        elif method == "PUT":
            code, data = put_json(url, payload)
        elif method == "DELETE":
            code, data = delete_json(url)
        else:
            return 0, {"error": f"Unsupported method {method}"}
        if code == 200 or code == 201:
            return code, data
    # if all fail, return last attempt
    return code, data

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Accounts & Access",
    "Bulk Import / Update",
    "Corrections & Flags",
    "Configs & Retention",
])

# ======================================================================================
# TAB 1 — ACCOUNTS & ACCESS
# ======================================================================================
with tab1:
    st.subheader("Accounts & Access")

    cA, cB = st.columns([2, 3])

    with cA:
        st.markdown("**Create account**")
        first = st.text_input("First name", "Liam", key="acc_first")
        last  = st.text_input("Last name", "Miller", key="acc_last")
        email = st.text_input("Email", "liam@example.com", key="acc_email")
        role  = st.selectbox("Role", ["sales", "ops", "admin"], index=1, key="acc_role")
        active = st.checkbox("Active", True, key="acc_active")

        if st.button("Create account", type="primary", use_container_width=True):
            payload = {
                "firstName": first, "lastName": last, "email": email,
                "role": role, "active": bool(active),
            }
            # Preferred endpoint → fallback to generic insert
            endpoints = [
                (f"{API_OAM}/accounts", payload),
                (f"{API_OAM}/insert", {"entity": "account", **payload}),
            ]
            code, data = try_endpoints("POST", endpoints)
            if code in (200, 201):
                st.success(f"Created: {data}")
            else:
                st.error(f"Create failed: {code} {data}")

        st.divider()
        st.markdown("**Access requests (from Sales)**")
        code, data = try_endpoints("GET", [
            (f"{API_OAM}/requests?type=access&status=open", None),
            (f"{API_OAM}/requests?status=open", None),
        ])
        if code == 200 and isinstance(data, list) and data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            sel = st.number_input("Request ID to approve/deny", min_value=1, step=1)
            action = st.selectbox("Action", ["approve", "deny"])
            if st.button("Apply"):
                p = {"action": action}
                c2, d2 = try_endpoints("PUT", [
                    (f"{API_OAM}/requests/{int(sel)}", p),
                ])
                st.success(d2) if c2 == 200 else st.error(f"{c2} {d2}")
        else:
            st.info("No open access requests or endpoint not available.")

    with cB:
        st.markdown("**Accounts**")
        limit = st.slider("Limit", 10, 500, 100, 10, key="acc_limit")
        code, data = try_endpoints("GET", [
            (f"{API_OAM}/accounts?limit={limit}", None),
            (f"{API_OAM}/users?limit={limit}", None),
        ])
        if code == 200 and isinstance(data, list) and data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption("Enable/disable or update role:")

            uid = st.number_input("Account/User ID", min_value=1, step=1, key="acc_uid")
            new_role = st.selectbox("New role", ["sales", "ops", "admin"], index=1, key="acc_newrole")
            is_active = st.checkbox("Active", True, key="acc_newactive")

            colx, coly = st.columns(2)
            if colx.button("Update role/active", use_container_width=True):
                payload = {"role": new_role, "active": bool(is_active)}
                c3, d3 = try_endpoints("PUT", [
                    (f"{API_OAM}/accounts/{int(uid)}", payload),
                ])
                st.success(d3) if c3 == 200 else st.error(f"{c3} {d3}")

            if coly.button("Delete account", use_container_width=True):
                c4, d4 = try_endpoints("DELETE", [
                    (f"{API_OAM}/accounts/{int(uid)}", None),
                ])
                st.success(d4) if c4 == 200 else st.error(f"{c4} {d4}")
        else:
            st.info("No accounts returned or endpoint not available.")

# ======================================================================================
# TAB 2 — BULK IMPORT / UPDATE
# ======================================================================================
with tab2:
    st.subheader("Bulk Import / Update")

    entity = st.selectbox("Entity type", ["Regions", "Buildings", "Spots"], index=2)
    mode = st.segmented_control("Mode", ["Insert", "Update"], default="Insert")

    uploaded = st.file_uploader("Upload CSV or JSON", type=["csv", "json"])
    sample_tip = st.expander("Field hints (minimum required)")
    with sample_tip:
        st.markdown(
            """
**Regions**: `regionName`  
**Buildings**: `buildingName`, `address`, `regionID`  
**Spots**: `address`, `price`, `status` (free|inuse|planned|w.issue), `latitude`, `longitude`  
Optional (Spots): `imageURL`, `estViewPerMonth`, `monthlyRentCost`, `contactTel`, `endTimeOfCurrentOrder`
            """
        )

    df = None
    if uploaded:
        try:
            if uploaded.type.endswith("json"):
                data = json.load(uploaded)
                df = pd.DataFrame(data if isinstance(data, list) else [data])
            else:
                # CSV
                df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Parse error: {e}")

    if df is not None and not df.empty:
        st.markdown("**Preview**")
        st.dataframe(df.head(25), use_container_width=True, hide_index=True)

        # Basic validation rules
        def validate_row(row, kind):
            missing = []
            if kind == "Regions":
                for k in ["regionName"]:
                    if pd.isna(row.get(k, None)): missing.append(k)
            elif kind == "Buildings":
                for k in ["buildingName", "address", "regionID"]:
                    if pd.isna(row.get(k, None)): missing.append(k)
            elif kind == "Spots":
                for k in ["address", "price", "status", "latitude", "longitude"]:
                    if pd.isna(row.get(k, None)): missing.append(k)
            return missing

        # Validate
        errs = []
        for i, row in df.iterrows():
            m = validate_row(row, entity)
            if m: errs.append((i, m))
        if errs:
            st.error(f"Validation failed on {len(errs)} rows (showing first 10):")
            st.write(errs[:10])
        else:
            st.success("Validation passed ✅")

            # Commit
            if st.button(("Insert" if mode=="Insert" else "Update") + f" {len(df)} {entity[:-1]}"):
                # Prefer a bulk endpoint, fallback to /insert per-row
                payload_list = df.to_dict(orient="records")
                if entity == "Regions":
                    target = "regions"
                elif entity == "Buildings":
                    target = "buildings"
                else:
                    target = "spots"

                # Try bulk first
                bulk_url = f"{API_OAM}/bulk_import?entity={target}&mode={mode.lower()}"
                code, data = post_json(bulk_url, payload_list)
                if code in (200, 201):
                    st.success(f"Bulk {mode.lower()} OK: {data}")
                else:
                    # fallback: per-row insert/update
                    successes, failures = 0, 0
                    prog = st.progress(0, text="Processing...")
                    for i, row in enumerate(payload_list, start=1):
                        if mode == "Insert":
                            per_code, per_data = post_json(f"{API_OAM}/insert", {"entity": target[:-1] if target.endswith('s') else target, **row})
                        else:
                            # must have an identifier to update; guess keys
                            identifier = (
                                row.get("spotID") or row.get("buildingID") or row.get("regionID") or row.get("id")
                            )
                            if identifier is None:
                                failures += 1
                                prog.progress(i/len(payload_list), text=f"Skip row {i} (no identifier)")
                                continue
                            per_code, per_data = put_json(f"{API_OAM}/{target}/{int(identifier)}", row)

                        if per_code in (200, 201):
                            successes += 1
                        else:
                            failures += 1
                        prog.progress(i/len(payload_list), text=f"Processed {i}/{len(payload_list)}")
                    st.info(f"Done. Success: {successes}, Fail: {failures}")

    else:
        st.info("Upload a CSV/JSON to continue.")

# ======================================================================================
# TAB 3 — CORRECTIONS & FLAGS
# ======================================================================================
with tab3:
    st.subheader("Corrections & Flags")

    # Try different plausible endpoints for the queue
    code, data = try_endpoints("GET", [
        (f"{API_OAM}/corrections?status=open", None),
        (f"{API_OAM}/invalid_spot_reports?status=open", None),
        (f"{API_OAM}/invalid?status=open", None),
    ])
    if code == 200 and isinstance(data, list) and data:
        dfq = pd.DataFrame(data)
        st.dataframe(dfq, use_container_width=True, hide_index=True)
        st.caption("Pick a correction to act on:")
        cid = st.number_input("Correction/Report ID", min_value=1, step=1)

        st.markdown("**Action**")
        action = st.selectbox("Choose", ["apply_fix", "needs_follow_up", "resolve"], index=0)
        with st.form("corr_form"):
            new_values = st.text_area("New values (optional JSON)", placeholder='{"address":"123 New St"}')
            submitted = st.form_submit_button("Submit", type="primary")
        if submitted:
            payload = {"action": action}
            if new_values.strip():
                try:
                    payload["values"] = json.loads(new_values)
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")
                    st.stop()
            c2, d2 = try_endpoints("PUT", [
                (f"{API_OAM}/corrections/{int(cid)}", payload),
                (f"{API_OAM}/invalid_spot_reports/{int(cid)}", payload),
            ])
            st.success(d2) if c2 == 200 else st.error(f"{c2} {d2}")
    else:
        st.info("No open corrections, or endpoint not available.")
        st.caption("Tip: you can also toggle a spot to 'w.issue' on the Spots Manager page and submit a correction here once available.")

# ======================================================================================
# TAB 4 — CONFIGS & RETENTION
# ======================================================================================
with tab4:
    st.subheader("System Configs & Data Retention")

    # Load current config (if endpoint exists)
    code, cfg = try_endpoints("GET", [
        (f"{API_OAM}/config", None),
    ])
    if code != 200 or not isinstance(cfg, dict):
        cfg = {
            "default_discount_cap_pct": 15,
            "alert_threshold_views": 50000,
            "placeholder_api_key": "",
            "retention_days_logs": 90,
            "retention_days_temp": 30,
        }
        st.info("Using local defaults (config endpoint not available).")

    c1, c2, c3 = st.columns(3)
    with c1:
        disc = st.number_input("Default discount cap (%)", 0, 90, int(cfg.get("default_discount_cap_pct", 15)))
        views = st.number_input("Alert threshold (monthly views)", 0, 10_000_000, int(cfg.get("alert_threshold_views", 50000)))
    with c2:
        key  = st.text_input("Placeholder API key", cfg.get("placeholder_api_key", ""))
        logs = st.number_input("Retention — logs (days)", 0, 3650, int(cfg.get("retention_days_logs", 90)))
    with c3:
        temp = st.number_input("Retention — temp data (days)", 0, 3650, int(cfg.get("retention_days_temp", 30)))
        today = st.date_input("Reference date", value=date.today())

    if st.button("Save config", type="primary"):
        payload = {
            "default_discount_cap_pct": int(disc),
            "alert_threshold_views": int(views),
            "placeholder_api_key": key,
            "retention_days_logs": int(logs),
            "retention_days_temp": int(temp),
            "reference_date": str(today),
        }
        c3, d3 = try_endpoints("PUT", [
            (f"{API_OAM}/config", payload),
            (f"{API_OAM}/insert", {"entity": "config", **payload}),  # last-resort fallback
        ])
        st.success(d3) if c3 == 200 else st.error(f"{c3} {d3}")

    st.divider()
    st.markdown("**Retention tools**")
    colA, colB = st.columns(2)

    with colA:
        older = st.number_input("Purge test/temporary orders older than N days", 7, 3650, 120)
        if st.button("Purge now"):
            c4, d4 = try_endpoints("POST", [
                (f"{API_OAM}/retention/purge?older_than_days={int(older)}", None),
            ])
            st.success(d4) if c4 in (200, 201) else st.error(f"{c4} {d4}")

    with colB:
        if st.button("Archive logs (zip & rotate)"):
            c5, d5 = try_endpoints("POST", [
                (f"{API_OAM}/retention/archive", None),
            ])
            st.success(d5) if c5 in (200, 201) else st.error(f"{c5} {d5}")
