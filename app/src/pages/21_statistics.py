# pages/Statistics.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from modules.nav import SideBarLinks

SideBarLinks()

st.title('Statistics')

def donut_chart(pct: float, center_text: str = ""):
    """Render a donut chart from 0.0–1.0 with center text."""
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
        st.selectbox(" ", ["Last 90 days", "Last 30 days", "Year to date"], label_visibility="collapsed", index=0)
    with c2:
        st.caption("Region")
        st.multiselect(" ", ["West town", "East town", "South"], default=["West town", "East town", "South"],
                       label_visibility="collapsed")
    with c3:
        st.caption(" ")
        st.button("Refresh", type="primary", use_container_width=True)

st.divider()

top_l, top_r = st.columns([3, 1])
with top_l:
    st.subheader("Overview")

with top_r:
    with st.container(border=True):
        st.caption("Owner")
        st.write("**Bob**")

left, right = st.columns(2)

with left:
    with st.container(border=True):
        st.caption("In-use Spot Ratio")
        donut_chart(0.92, "92%")

    with st.container(border=True):
        st.caption("Order count (last 90 days)")
        st.metric(label="Orders", value=124, delta="+20 MoM")

# Right column: satisfaction + VIP reorders
with right:
    with st.container(border=True):
        st.caption("Customer Satisfaction (last 90 days)")
        a, b, c = st.columns(3)
        a.metric("West town", "4.3 / 5")
        b.metric("East town", "4.1 / 5")
        c.metric("South", "4.5 / 5")

    with st.container(border=True):
        st.caption("VIP Re-order Count (last 90 days)")
        vip_df = pd.DataFrame(
            [{"VIP": "Wassle K.", "Reorders": 7},
             {"VIP": "Sun L.", "Reorders": 3}]
        )
        st.dataframe(vip_df, use_container_width=True, hide_index=True)

st.divider()

# Optional: quick snapshot cards like your other pages
with st.container(border=True):
    st.caption("Snapshot")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Spots: Total", 1055)
    m2.metric("Spots: In-use", 840)
    m3.metric("Spots: Free", 133)
    m4.metric("Spots: W.Issue", 82)
