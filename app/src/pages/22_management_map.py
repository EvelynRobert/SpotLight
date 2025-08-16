import streamlit as st
import pandas as pd
import numpy as np
import requests
import pydeck as pdk
from datetime import date
from modules.nav import SideBarLinks

API_URL = "http://web-api:4000/o_and_m"

SideBarLinks()
st.set_page_config(layout="wide")
st.title("O&M Spots Dashboard")

@st.cache_data(ttl=30)
def load_spots():
    df = None
    try:
        r = requests.get(f"{API_URL}/spots/summary?limit=40", timeout=10)
        if r.status_code == 200:
            data = r.json()
            df = pd.DataFrame(data)
            if not df.empty and 0 in df.columns:
                df.columns = ["spotID","address","status","price","estViewPerMonth","monthlyRentCost"]
    except Exception:
        pass

    if "latitude" in df.columns and "longitude" in df.columns:
        df = df.rename(columns={"latitude":"lat","longitude":"lon"})
    else:
        center_lat, center_lon = 29.6516, -82.3248
        rng = np.random.default_rng(42)
        df["lat"] = center_lat + rng.normal(0, 0.02, len(df))
        df["lon"] = center_lon + rng.normal(0, 0.02, len(df))

    df["imageURL"] = "https://images.unsplash.com/photo-1517148815978-75f6acaaf32c?q=80&w=1600&auto=format&fit=crop"  # demo
    df["contactTel"] = "434-355-4335"
    df["contactName"] = "David K."
    df["untilDate"] = date.today().replace(year=date.today().year + 1)
    return df

spots_df = load_spots()
spot_options = spots_df["spotID"].tolist()
sel_id = st.selectbox("Select Spot", spots_df["spotID"].tolist())
sel = spots_df.loc[spots_df["spotID"] == sel_id].iloc[0]

base_df = pd.DataFrame({
    "lon": spots_df["lon"].astype(float),
    "lat": spots_df["lat"].astype(float),
    "color": [[30, 30, 30, 200]] * len(spots_df),
})

selected_df = pd.DataFrame([{
    "lon": float(sel["lon"]),
    "lat": float(sel["lat"]),
    "color": [220, 20, 60, 240],
}])

view_state = pdk.ViewState(
    latitude=float(sel["lat"]),
    longitude=float(sel["lon"]),
    zoom=11,
    pitch=0,
)

base = pdk.Layer(
    "ScatterplotLayer",
    data=base_df,
    get_position=["lon", "lat"],
    get_radius=120,
    get_fill_color="color",
    pickable=False,
)

selected_layer = pdk.Layer(
    "ScatterplotLayer",
    data=selected_df,
    get_position=["lon", "lat"],
    get_radius=180,
    get_fill_color="color",
    pickable=False,
)

st.pydeck_chart(
    pdk.Deck(
        layers=[base, selected_layer],
        initial_view_state=view_state,
        map_style=None,
    )
)

with st.container(border=True):
    st.image(sel["imageURL"], use_container_width=True)

    st.write("")
    b1, b2, b3, b4 = st.columns(4, gap="small")
    if b1.button("In Use", type=("primary" if sel["status"] == "inuse" else "secondary"), use_container_width=True):
        try:
            r = requests.put(f"{API_URL}/spots/{sel_id}/status", json={"status":"inuse"}, timeout=10)
            st.toast("Status updated" if r.status_code == 200 else f"Error {r.status_code}")
        except Exception:
            st.toast("Backend not reachable")
    if b2.button("Free", type=("primary" if sel["status"] == "free" else "secondary"), use_container_width=True):
        try:
            r = requests.put(f"{API_URL}/spots/{sel_id}/status", json={"status":"free"}, timeout=10)
            st.toast("Status updated" if r.status_code == 200 else f"Error {r.status_code}")
        except Exception:
            st.toast("Backend not reachable")
    if b3.button("W.Issue", type=("primary" if sel["status"] == "w.issue" else "secondary"), use_container_width=True):
        try:
            r = requests.put(f"{API_URL}/spots/{sel_id}/status", json={"status":"w.issue"}, timeout=10)
            st.toast("Status updated" if r.status_code == 200 else f"Error {r.status_code}")
        except Exception:
            st.toast("Backend not reachable")
    if b4.button("Planned", type=("primary" if sel["status"] == "planned" else "secondary"), use_container_width=True):
        try:
            r = requests.put(f"{API_URL}/spots/{sel_id}/status", json={"status":"planned"}, timeout=10)
            st.toast("Status updated" if r.status_code == 200 else f"Error {r.status_code}")
        except Exception:
            st.toast("Backend not reachable")

    st.write("")
    new_price = st.number_input("Edit Price", min_value=0, value=int(sel["price"]), key="price")
    if st.button("Update", key="u_price", use_container_width=True):
        st.toast("Price update: placeholder")

    new_until = st.date_input("Edit Until", value=sel["untilDate"], key="until")
    if st.button("Update", key="u_until", use_container_width=True):
        st.toast("Until update: placeholder")

    new_addr = st.text_input("Edit Address", value=str(sel["address"]), key="addr")
    if st.button("Update", key="u_addr", use_container_width=True):
        st.toast("Address update: placeholder")

    st.write("")
    displayed = st.container()
    with displayed:
        st.success(f"{int(sel['estViewPerMonth'])}")
    new_evm = st.number_input("Edit Estimated Views/Month", min_value=0, value=int(sel["estViewPerMonth"]), key="evm")
    if st.button("Update", key="u_evm", use_container_width=True):
        st.toast("Estimated views update: placeholder")

with st.container(border=True):
    st.subheader("Fixed Info", anchor=False)
    st.text_input("ID", f"{int(sel['spotID']):06d}", disabled=True)
    st.text_input("Contact Tel", sel["contactTel"], disabled=True)
    st.text_input("Monthly Rent Cost", f"${int(sel['monthlyRentCost'])}", disabled=True)
    st.text_input("Contact Name", sel["contactName"], disabled=True)
