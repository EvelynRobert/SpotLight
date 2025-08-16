import streamlit as st
import pandas as pd
import requests
import pydeck as pdk


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


st.set_page_config(page_title="O&M Spots Manager", layout="wide")
st.title("O&M Spots Dashboard")

API_OAM = "http://web-api:4000/o_and_m"
API_SALESMAN = "http://web-api:4000/salesman"

# Gainesville defaults
DEFAULT_LAT, DEFAULT_LNG, DEFAULT_ZOOM = 29.6516, -82.3248, 12

def get_json(url):
    try:
        r = requests.get(url, timeout=20)
        if r.headers.get("content-type","").startswith("application/json"):
            return r.status_code, r.json()
        return r.status_code, r.text
    except Exception as e:
        return 0, {"error": str(e)}

def put_json(url, payload):
    try:
        r = requests.put(url, json=payload, timeout=20)
        if r.headers.get("content-type","").startswith("application/json"):
            return r.status_code, r.json()
        return r.status_code, r.text
    except Exception as e:
        return 0, {"error": str(e)}

# ----- filters -----
left, right = st.columns([1,3])
with left:
    status = st.selectbox("Status", ["any","free","inuse","planned","w.issue"], index=0)
    radius_km = st.slider("Radius (km)", 1, 20, 8)
    lat0 = st.number_input("Center lat", value=DEFAULT_LAT, format="%.6f")
    lng0 = st.number_input("Center lng", value=DEFAULT_LNG, format="%.6f")
    if st.button("Center on Gainesville"):
        lat0, lng0 = DEFAULT_LAT, DEFAULT_LNG
with right:
    st.caption("Use filters to fetch nearby spots. Click a point to see details in the table below.")

params = f"lat={lat0}&lng={lng0}&radius_km={radius_km}"
if status != "any":
    params += f"&status={status}"

code, data = get_json(f"{API_SALESMAN}/spots?{params}")
if code != 200 or not isinstance(data, list):
    st.error(f"Failed to load spots: {code} {data}")
    st.stop()

df = pd.DataFrame(data).rename(columns={"latitude":"lat","longitude":"lng"})
if df.empty:
    st.info("No spots returned for those filters.")
    st.stop()

# ----- map (force light basemap) -----
layer = pdk.Layer(
    "ScatterplotLayer",
    df,
    get_position="[lng, lat]",
    get_radius=60,
    pickable=True,
)
view_state = pdk.ViewState(latitude=float(lat0), longitude=float(lng0), zoom=DEFAULT_ZOOM)
st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_provider="carto",
        map_style="light",
        tooltip={"text": "{address}\nstatus: {status}"},
    )
)

# ----- table & quick status update -----
st.caption(f"{len(df)} spot(s) found")
show_cols = [c for c in ["spotID","address","lat","lng","status","price","estViewPerMonth","monthlyRentCost","contactTel","distance_km"] if c in df.columns]
st.dataframe(df[show_cols], use_container_width=True, hide_index=True)

st.subheader("Update spot status")
sid = st.number_input("spotID", min_value=1, step=1, value=int(df.iloc[0]["spotID"]))
new_status = st.selectbox("New status", ["free","inuse","planned","w.issue"], index=0)
if st.button("Update status", type="primary"):
    code, resp = put_json(f"{API_SALESMAN}/spots/{int(sid)}/status", {"status": new_status})
    if code in (200,204):
        st.success(f"Updated spot {int(sid)} to {new_status}. Refresh the list above to see it.")
    else:
        st.error(f"Update failed: {code} {resp}")
