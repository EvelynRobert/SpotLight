#01_Customer_Profile.py
import os, requests, streamlit as st


API = os.getenv("API_BASE_URL", "http://127.0.0.1:4000")

def api(method, path, **kw):
    url = f"{API.rstrip('/')}/{path.lstrip('/')}"
    try:
        r = requests.request(method, url, timeout=15, **kw)
        ct = r.headers.get("content-type","")
        data = r.json() if "application/json" in ct else r.text
        return r.status_code, data
    except Exception as e:
        return 0, {"error": str(e)}

st.set_page_config(page_title="Customer Profile", page_icon="👤", layout="wide")
st.title("👤 Customer Profile")

# ---- Quick nav to other Customer pages ----
from modules.nav import SideBarLinks
SideBarLinks()
            
# --- list / search ---
col_a, col_b = st.columns([2,1])
with col_a:
    q = st.text_input("Search customers (name/email)", "")
with col_b:
    if st.button("Refresh"):
        pass

code, data = api("GET", f"/customer/?q={q}") if q else api("GET", "/customer/")
if code != 200 or isinstance(data, dict) and data.get("error"):
    st.error(f"Failed to load customers: {data}")
    st.stop()

rows = data if isinstance(data, list) else []
if not rows:
    st.info("No customers found.")
    st.stop()

# pick one
options = {f"{r['cID']} — {r.get('fName','')} {r.get('lName','')}  <{r.get('email','')}>": r for r in rows}
label = st.selectbox("Select a customer", list(options.keys()))
cust = options[label]

left, right = st.columns(2)

with left:
    st.subheader("Details")
    st.json(cust, expanded=False)

    st.subheader("Orders")
    oc, odata = api("GET", f"/customer/{cust['cID']}/orders")
    if oc == 200:
        st.dataframe(odata, hide_index=True, use_container_width=True)
    else:
        st.warning(f"Could not load orders: {odata}")

with right:
    st.subheader("Actions")

    # Delete (uses your working DELETE /customer/<id>)
    st.divider()
    if st.button("🗑️ Delete this customer", type="primary"):
        dc, ddata = api("DELETE", f"/customer/{cust['cID']}")
        if dc == 200:
            st.success(f"Deleted cID={cust['cID']}. Click Refresh above.")
        else:
            st.error(f"Delete failed: {dc} {ddata}")
