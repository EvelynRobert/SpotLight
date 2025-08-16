# pages/Statistics.py
import streamlit as st
import pandas as pd
import requests

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


st.set_page_config(page_title="O&M Statistics", layout="wide")
st.title("Statistics")

API_OAM = "http://web-api:4000/o_and_m"

def get_json(url):
    try:
        r = requests.get(url, timeout=20)
        if r.headers.get("content-type","").startswith("application/json"):
            return r.status_code, r.json()
        return r.status_code, r.text
    except Exception as e:
        return 0, {"error": str(e)}

period = st.segmented_control("Period", ["7d","30d","90d","180d"], default="90d")
st.caption("Metrics use the selected period where applicable (orders).")

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("Spots")
    code, data = get_json(f"{API_OAM}/spots/metrics")
    if code == 200 and isinstance(data, dict):
        a,b,c = st.columns(3)
        a.metric("Total", data.get("total",0))
        b.metric("In use", data.get("in_use",0))
        c.metric("With issue", data.get("with_issue",0))
    else:
        st.error(f"{code} {data}")

with c2:
    st.subheader("Customers")
    code, data = get_json(f"{API_OAM}/customers/metrics")
    if code == 200 and isinstance(data, dict):
        a,b,c = st.columns(3)
        a.metric("Total", data.get("total",0))
        b.metric("VIP", data.get("vip",0))
        c.metric("Never ordered", data.get("never_ordered",0))
        st.caption(f"Avg days since last order: {round(data.get('avg_days',0),2)}")
    else:
        st.error(f"{code} {data}")

with c3:
    st.subheader("Orders")
    code, data = get_json(f"{API_OAM}/orders/metrics?period={period}")
    if code == 200 and isinstance(data, dict):
        a,b = st.columns(2)
        a.metric("All time total", data.get("total",0))
        b.metric("Avg order $", round(data.get("avg_price",0),2) if data.get("avg_price") is not None else 0)
        st.caption(f"Orders in {period}: {data.get('last_period',0)}")
    else:
        st.error(f"{code} {data}")

st.divider()
t1, t2, t3 = st.tabs(["Recent spots", "Recent customers", "Recent orders"])

with t1:
    code, data = get_json(f"{API_OAM}/spots/summary?limit=25")
    if code == 200 and isinstance(data, list) and data:
        df = pd.DataFrame(data)
        show = [c for c in ["spotID","address","status","price","estViewPerMonth","monthlyRentCost"] if c in df.columns]
        st.dataframe(df[show], use_container_width=True, hide_index=True)
    else:
        st.info("No data.")

with t2:
    code, data = get_json(f"{API_OAM}/customers/summary?limit=25")
    if code == 200 and isinstance(data, list) and data:
        df = pd.DataFrame(data)
        show = [c for c in ["cID","fName","lName","email","companyName","VIP","last_order_date","days_since_last_order"] if c in df.columns]
        st.dataframe(df[show], use_container_width=True, hide_index=True)
    else:
        st.info("No data.")

with t3:
    code, data = get_json(f"{API_OAM}/orders/summary?period={period}&limit=25")
    if code == 200 and isinstance(data, list) and data:
        df = pd.DataFrame(data)
        show = [c for c in ["orderID","date","total","cID"] if c in df.columns]
        st.dataframe(df[show], use_container_width=True, hide_index=True)
    else:
        st.info("No data.")
