# 30_Owner_Home.py
import os, sys, requests, pandas as pd, streamlit as st

# --- make parent (app/src) importable, then load sidebar ---
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from modules.nav import SideBarLinks
except Exception:
    def SideBarLinks():
        with st.sidebar:
            st.page_link("Home.py", label="🏠 Home")

st.set_page_config(page_title="Owner • Dashboard", page_icon="📊", layout="wide")
SideBarLinks()
st.title("📊 Owner Dashboard")

API = os.getenv("API_BASE_URL", "http://127.0.0.1:4000").rstrip("/")

def api(method: str, path: str, **kw):
    url = f"{API}/{path.lstrip('/')}"
    try:
        r = requests.request(method, url, timeout=25, **kw)
        data = r.json() if "application/json" in r.headers.get("content-type","") else r.text
        return r.status_code, data
    except Exception as e:
        return 0, {"error": str(e)}

# ---- Try Owner overview; fall back to O&M metrics if not present ----
code, overview = api("GET", "/owner/overview")
if code != 200 or not isinstance(overview, dict):
    overview = {}
    sc, s = api("GET", "/o_and_m/spots/metrics")
    cc, c = api("GET", "/o_and_m/customers/metrics")
    oc, o = api("GET", "/o_and_m/orders/metrics?period=90d")
    if sc == 200 and isinstance(s, dict): overview.update({"spots_total": s.get("total",0), "spots_in_use": s.get("in_use",0), "spots_with_issue": s.get("with_issue",0)})
    if cc == 200 and isinstance(c, dict): overview.update({"vip_count": c.get("vip",0)})
    if oc == 200 and isinstance(o, dict): overview.update({"revenue_90d": o.get("sum_total", o.get("last_period_total", 0)), "avg_order_value": o.get("avg_price", 0)})

# ---- KPI cards ----
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Spots", overview.get("spots_total", 0))
k2.metric("In Use", overview.get("spots_in_use", 0))
k3.metric("With Issue", overview.get("spots_with_issue", 0))
k4.metric("VIP Customers", overview.get("vip_count", 0))
k5.metric("Revenue (90d)", f"${overview.get('revenue_90d', 0):,.0f}")
k6.metric("Avg Order $", f"${overview.get('avg_order_value', 0):,.2f}")

st.divider()

# ---- Region heat (Owner API preferred; graceful fallback) ----
st.subheader("Regions — spots, in-use %, revenue (90d)")
rc, rdata = api("GET", "/owner/regions/rollup?period=90d")
if rc == 200 and isinstance(rdata, list) and rdata:
    df_regions = pd.DataFrame(rdata)
    want = [c for c in ["region","spots_total","in_use_pct","revenue_90d","orders_90d","views_90d"] if c in df_regions.columns]
    st.dataframe(df_regions[want], use_container_width=True, hide_index=True)
else:
    st.info("Region rollup not available yet. (Add /owner/regions/rollup or extend O&M summaries to include regions.)")

st.divider()

# ---- Top lists ----
cA, cB = st.columns(2)

with cA:
    st.subheader("Top 10 Clients by Spend (90d)")
    oc, odata = api("GET", "/o_and_m/orders/summary?period=90d&limit=10000")
    if oc == 200 and isinstance(odata, list) and odata:
        df = pd.DataFrame(odata)
        if "cID" in df.columns and "total" in df.columns:
            top = (df.groupby("cID")["total"].sum().reset_index().sort_values("total", ascending=False).head(10))
            # try to fetch names for the top 10 (best-effort)
            names = {}
            for cid in top["cID"].tolist():
                nc, ndata = api("GET", f"/customer/{int(cid)}")
                if nc == 200 and isinstance(ndata, dict):
                    nm = f"{ndata.get('fName','')} {ndata.get('lName','')}".strip()
                    if ndata.get("companyName"):
                        nm = f"{nm} ({ndata.get('companyName')})" if nm else ndata.get("companyName")
                    names[cid] = nm or f"Customer {cid}"
                else:
                    names[cid] = f"Customer {cid}"
            top["customer"] = top["cID"].map(names)
            top = top[["customer","cID","total"]]
            top["total"] = top["total"].map(lambda x: f"${x:,.0f}")
            st.dataframe(top, use_container_width=True, hide_index=True)
        else:
            st.info("Orders summary missing cID/total fields.")
    else:
        st.info("No order data for last 90 days.")

with cB:
    st.subheader("Top 10 Regions (orders/views)")
    if rc == 200 and isinstance(rdata, list) and rdata:
        dfR = pd.DataFrame(rdata)
        if "orders_90d" in dfR.columns:
            show_orders = dfR.sort_values("orders_90d", ascending=False).head(10)[["region","orders_90d"]]
            st.markdown("**By orders (90d)**")
            st.dataframe(show_orders, use_container_width=True, hide_index=True)
        if "views_90d" in dfR.columns:
            show_views = dfR.sort_values("views_90d", ascending=False).head(10)[["region","views_90d"]]
            st.markdown("**By views (90d)**")
            st.dataframe(show_views, use_container_width=True, hide_index=True)
    else:
        st.info("Region rollup not available to rank regions yet.")

st.divider()

# ---- Quick links to Owner pages ----
st.subheader("Quick Links")
b1, b2, b3 = st.columns(3)
with b1:
    st.page_link("pages/31_Owner_Deals_and_Knowledge.py", label="📚 Deals & Knowledge")
with b2:
    st.page_link("pages/32_Owner_Pricing_and_Discounts.py", label="💸 Pricing & Discounts")
with b3:
    st.page_link("pages/33_Owner_Reviews_VIP_and_Hygiene.py", label="⭐ Reviews, VIP & Hygiene")
