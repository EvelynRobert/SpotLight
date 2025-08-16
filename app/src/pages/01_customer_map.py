import streamlit as st
import pandas as pd
import numpy as np
import requests
import pydeck as pdk
from datetime import date
from modules.nav import SideBarLinks

API_URL = "http://web-api:4000/o_and_m"

st.title("Customer Map")
SideBarLinks()

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

    df["imageURL"] = "https://images.unsplash.com/photo-1517148815978-75f6acaaf32c?q=80&w=1600&auto=format&fit=crop"
    df["contactTel"] = "434-355-4335"
    df["contactName"] = "David K."
    df["untilDate"] = date.today().replace(year=date.today().year + 1)
    return df

spots_df = load_spots()

if "cart" not in st.session_state:
    st.session_state.cart = []

if not spots_df.empty:
    spot_choice = st.selectbox("Select a Spot", spots_df["address"])
    spot = spots_df[spots_df["address"] == spot_choice].iloc[0]

    base_df = pd.DataFrame({
        "lon": spots_df["lon"].astype(float),
        "lat": spots_df["lat"].astype(float),
        "color": [[30, 30, 30, 200]] * len(spots_df),
    })

    selected_df = pd.DataFrame([{
        "lon": float(spot["lon"]),
        "lat": float(spot["lat"]),
        "color": [220, 20, 60, 240],
    }])

    view_state = pdk.ViewState(
        latitude=float(spot["lat"]),
        longitude=float(spot["lon"]),
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
        cols = st.columns([1,2])
        with cols[0]:
            st.image(spot["imageURL"], use_container_width=True)
        with cols[1]:
            st.write(f"**Estimated view:** {spot['estViewPerMonth']}")
            st.write(f"Price: **${spot['price']} / month**")
            st.write(spot["address"])
            c1, c2 = st.columns([1,1])
            with c1:
                st.button("Favorite", key=f"fav_{spot['spotID']}", use_container_width=True)
            with c2:
                if st.button("Add to Order", key=f"add_{spot['spotID']}", use_container_width=True):
                    st.session_state.cart.append(spot.to_dict())
                    st.toast("Added to cart")

with st.container(border=True):
    st.write("### Cart")
    if st.session_state.cart:
        subtotal = sum([c["price"] for c in st.session_state.cart])
        st.caption(f"Subtotal: ${subtotal}")
        for item in st.session_state.cart:
            st.write(f"⭐ {item['address']} — ${item['price']}")
        c1, c2 = st.columns([1,1])
        if c1.button("Clear Cart", use_container_width=True):
            st.session_state.cart.clear()
            st.rerun()
        if c2.button("Proceed", type="primary", use_container_width=True):
            st.toast("Proceeding to checkout…")
    else:
        st.info("Cart is empty")
