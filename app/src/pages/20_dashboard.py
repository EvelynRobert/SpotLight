import streamlit as st
import pandas as pd
import requests
from datetime import date

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


# --- API bases pulled from env so this works inside/outside Docker ---
import os
BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:4000")     # <— set this in your terminal or .env
API_OAM = f"{BASE.rstrip('/')}/o_and_m"
API_SALESMAN = f"{BASE.rstrip('/')}/salesman"
API_OWNER = f"{BASE.rstrip('/')}/owner"


st.set_page_config(page_title="O&M Dashboard", layout="wide")
st.title("O&M Dashboard")

API_OAM = "http://web-api:4000/o_and_m"
API_SALESMAN = "http://web-api:4000/salesman"

# -------- helpers --------
def get_json(url):
    try:
        r = requests.get(url, timeout=20)
        if r.headers.get("content-type","").startswith("application/json"):
            return r.status_code, r.json()
        return r.status_code, r.text
    except Exception as e:
        return 0, {"error": str(e)}

def post_json(url, payload):
    try:
        r = requests.post(url, json=payload, timeout=20)
        if r.headers.get("content-type","").startswith("application/json"):
            return r.status_code, r.json()
        return r.status_code, r.text
    except Exception as e:
        return 0, {"error": str(e)}

# -------- top metrics --------
m1, m2, m3 = st.columns(3)

with m1:
    st.subheader("Spots")
    code, data = get_json(f"{API_OAM}/spots/metrics")
    if code == 200 and isinstance(data, dict):
        a,b,c = st.columns(3)
        a.metric("Total", data.get("total",0))
        b.metric("In use", data.get("in_use",0))
        c.metric("With issue", data.get("with_issue",0))
    else:
        st.error(f"Spots metrics error: {code} {data}")

with m2:
    st.subheader("Customers")
    code, data = get_json(f"{API_OAM}/customers/metrics")
    if code == 200 and isinstance(data, dict):
        a,b,c = st.columns(3)
        a.metric("Total", data.get("total",0))
        b.metric("VIP", data.get("vip",0))
        c.metric("Never ordered", data.get("never_ordered",0))
        st.caption(f"Avg days since last order: {round(data.get('avg_days',0),2)}")
    else:
        st.error(f"Customers metrics error: {code} {data}")

with m3:
    st.subheader("Orders (90d)")
    code, data = get_json(f"{API_OAM}/orders/metrics?period=90d")
    if code == 200 and isinstance(data, dict):
        a,b = st.columns(2)
        a.metric("All time total", data.get("total",0))
        b.metric("Avg order $", round(data.get("avg_price",0),2) if data.get("avg_price") is not None else 0)
        st.caption(f"Orders in last 90 days: {data.get('last_period',0)}")
    else:
        st.error(f"Orders metrics error: {code} {data}")

st.divider()

# -------- tabs: info & quick create --------
tab1, tab2, tab3, tab4 = st.tabs(["Spots info", "Customer accounts info", "Order info", "Quick insert"])

with tab1:
    st.subheader("Spots info (latest)")
    limit = st.slider("Limit", 10, 200, 50, 10, key="spots_limit")
    code, data = get_json(f"{API_OAM}/spots/summary?limit={limit}")
    if code == 200 and isinstance(data, list) and data:
        df = pd.DataFrame(data)
        show = [c for c in ["spotID","address","status","price","estViewPerMonth","monthlyRentCost"] if c in df.columns]
        st.dataframe(df[show], use_container_width=True, hide_index=True)
    else:
        st.info("No spots found or endpoint returned none.")

with tab2:
    st.subheader("Customer accounts info")
    limit = st.slider("Limit", 10, 200, 50, 10, key="cust_limit")
    code, data = get_json(f"{API_OAM}/customers/summary?limit={limit}")
    if code == 200 and isinstance(data, list) and data:
        df = pd.DataFrame(data)
        show = [c for c in ["cID","fName","lName","email","companyName","VIP","last_order_date","days_since_last_order"] if c in df.columns]
        st.dataframe(df[show], use_container_width=True, hide_index=True)
    else:
        st.info("No customers found or endpoint returned none.")

with tab3:
    st.subheader("Order info (recent 90d)")
    limit = st.slider("Limit", 10, 200, 50, 10, key="orders_limit")
    code, data = get_json(f"{API_OAM}/orders/summary?period=90d&limit={limit}")
    if code == 200 and isinstance(data, list) and data:
        df = pd.DataFrame(data)
        show = [c for c in ["orderID","date","total","cID"] if c in df.columns]
        st.dataframe(df[show], use_container_width=True, hide_index=True)
    else:
        st.info("No orders in period or endpoint returned none.")

with tab4:
    st.subheader("Quick insert")
    sub = st.segmented_control("Entity", ["Spot","Customer","Order"], key="ins_seg")

    if sub == "Spot":
        col = st.columns(3)
        price = col[0].number_input("price", 0, 10_000, 500)
        contactTel = col[1].text_input("contactTel", "000-000-0000")
        address = col[2].text_input("address", "123 Main St, Gainesville, FL")
        more = st.expander("Optional fields")
        with more:
            status = st.selectbox("status", ["free","inuse","planned","w.issue"], index=0)
            imageURL = st.text_input("imageURL", "")
            estViewPerMonth = st.number_input("estViewPerMonth", 0, 10_000_000, 1000)
            monthlyRentCost = st.number_input("monthlyRentCost", 0, 10_000, 0)
            endTimeOfCurrentOrder = st.text_input("endTimeOfCurrentOrder", "")
            latitude = st.number_input("latitude", value=29.6516, format="%.6f")
            longitude = st.number_input("longitude", value=-82.3248, format="%.6f")
        if st.button("Create spot", type="primary"):
            payload = {
                "entity":"spot","price":price,"contactTel":contactTel,"address":address,
                "status":status,"imageURL":imageURL or None,"estViewPerMonth":estViewPerMonth,
                "monthlyRentCost":monthlyRentCost,"endTimeOfCurrentOrder":endTimeOfCurrentOrder or None,
                "latitude":latitude,"longitude":longitude
            }
            code, data = post_json(f"{API_OAM}/insert", payload)
            st.success(data) if code in (200,201) else st.error(f"{code} {data}")

    if sub == "Customer":
        col = st.columns(3)
        fName = col[0].text_input("fName","Liam")
        lName = col[1].text_input("lName","Miller")
        email = col[2].text_input("email","liam@example.com")
        more = st.expander("Optional fields")
        with more:
            position = st.text_input("position","Analyst")
            companyName = st.text_input("companyName","Skyvu")
            totalOrderTimes = st.number_input("totalOrderTimes",0,1000,0)
            VIP = st.checkbox("VIP", False)
            avatarURL = st.text_input("avatarURL","")
            balance = st.number_input("balance",0,1_000_000,0)
            TEL = st.text_input("TEL","")
        if st.button("Create customer", type="primary"):
            payload = {
                "entity":"customer","fName":fName,"lName":lName,"email":email,
                "position":position,"companyName":companyName,"totalOrderTimes":int(totalOrderTimes),
                "VIP":bool(VIP),"avatarURL":avatarURL or None,"balance":int(balance),"TEL":TEL or None
            }
            code, data = post_json(f"{API_OAM}/insert", payload)
            st.success(data) if code in (200,201) else st.error(f"{code} {data}")

    if sub == "Order":
        col = st.columns(3)
        date_str = col[0].text_input("date (YYYY-MM-DD)", str(date.today()))
        total_amt = col[1].number_input("total", 0, 1_000_000, 0)
        cID = col[2].number_input("cID (customer id)", 1, 999999, 1)
        if st.button("Create order", type="primary"):
            payload = {"entity":"order","date":date_str,"total":int(total_amt),"cID":int(cID)}
            code, data = post_json(f"{API_OAM}/insert", payload)
            st.success(data) if code in (200,201) else st.error(f"{code} {data}")
