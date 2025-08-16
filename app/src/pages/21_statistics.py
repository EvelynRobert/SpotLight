# pages/Statistics.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import requests
from datetime import date
from modules.nav import SideBarLinks

API_URL = "http://web-api:4000/o_and_m"

SideBarLinks()
st.title('Statistics')

def donut_chart(pct: float, center_text: str = ""):
    pct = max(0.0, min(1.0, float(pct)))
    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.pie([pct, 1 - pct], startangle=90, wedgeprops=dict(width=0.35))
    ax.text(0, 0, center_text, ha="center", va="center", fontsize=18, fontweight="bold")
    ax.set(aspect="equal")
    ax.axis("off")
    st.pyplot(fig, use_container_width=False)

with st.container(border=True):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        st.caption("Time window")
        window = st.selectbox(" ", ["Last 90 days", "Last 30 days", "Year to date"], label_visibility="collapsed", index=0)
    with c2:
        st.caption("Region")
        st.multiselect(" ", ["West town", "East town", "South"], default=["West town", "East town", "South"], label_visibility="collapsed")
    with c3:
        st.caption(" ")
        st.button("Refresh", type="primary", use_container_width=True)

st.divider()

top_l, top_r = st.columns([3, 1])
with top_l:
    st.subheader("Overview")

left, right = st.columns(2)

# period mapping
if window == "Last 30 days":
    period = "30d"
elif window == "Last 90 days":
    period = "90d"
else:
    start = date(date.today().year, 1, 1)
    days = (date.today() - start).days + 1
    period = f"{days}d"

# fetch metrics
spots = None
orders = None
try:
    r = requests.get(f"{API_URL}/spots/metrics", timeout=10)
    if r.status_code == 200:
        spots = r.json()
except Exception:
    pass

try:
    r = requests.get(f"{API_URL}/orders/metrics", params={"period": period}, timeout=10)
    if r.status_code == 200:
        orders = r.json()
except Exception:
    pass

with left:
    with st.container(border=True):
        st.caption("In-use Spot Ratio")
        total = (spots or {}).get("total") or 0
        in_use = (spots or {}).get("in_use") or 0
        ratio = (in_use / total) if total else 0
        donut_chart(ratio, f"{round(ratio*100) if total else 0}%")

    with st.container(border=True):
        st.caption(f"Order count ({window.lower()})")
        st.metric(label="Orders", value=(orders or {}).get("last_period") or 0)

with right:
    with st.container(border=True):
        st.caption(f"Customer Satisfaction ({window.lower()})")
        a, b, c = st.columns(3)
        a.metric("West town", "4.3 / 5")
        b.metric("East town", "4.1 / 5")
        c.metric("South", "4.5 / 5")

    with st.container(border=True):
        st.caption(f"VIP Re-order Count ({window.lower()})")
        vip_df = pd.DataFrame(
            [{"VIP": "Wassle K.", "Reorders": 7},
             {"VIP": "Sun L.", "Reorders": 3}]
        )
        st.dataframe(vip_df, use_container_width=True, hide_index=True)

st.divider()

with st.container(border=True):
    st.caption("Snapshot")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Spots: Total", (spots or {}).get("total") or 0)
    m2.metric("Spots: In-use", (spots or {}).get("in_use") or 0)
    m3.metric("Spots: Free", (spots or {}).get("free") or 0)
    m4.metric("Spots: W.Issue", (spots or {}).get("with_issue") or 0)
