# pages/Sales_Workbench.py
import streamlit as st
from datetime import date, datetime, time
from modules.nav import SideBarLinks

SideBarLinks()

st.title('Sales Workbench')

if "orders" not in st.session_state:
    st.session_state.orders = {
        "ORD-001": {
            "customer": "Eric.C",
            "subtotal": 150,
            "tel": "323 748 2748",
            "order_times": 1,
            "position": 1,
            "duration_days": 30,
            "vip": False,
            "status": "New",
            "notes": "",
            "processed_on": None,     # date when marked processed
        },
        "ORD-002": {
            "customer": "Johnson.M",
            "subtotal": 700,
            "tel": "416 478 4222",
            "order_times": 3,
            "position": 3,
            "duration_days": 30,
            "vip": False,
            "status": "New",
            "notes": "",
            "processed_on": None,
        },
        "ORD-003": {
            "customer": "Lee.O",
            "subtotal": 2600,
            "tel": "788 028 7846",
            "order_times": 8,
            "position": 9,
            "duration_days": 60,
            "vip": True,
            "status": "New",
            "notes": "",
            "processed_on": None,
        },
    }

if "detail_order_id" not in st.session_state:
    st.session_state.detail_order_id = None

# -------------------- Helpers ----------------------
STATUSES = ["New", "Called", "Processing", "Awaiting Payment", "Processed", "Escalated"]

def info_box(label: str, value: str):
    with st.container(border=True):
        st.write(f"**{label}:** {value}")

def mark_processed(oid: str):
    st.session_state.orders[oid]["status"] = "Processed"
    st.session_state.orders[oid]["processed_on"] = date.today()
    st.toast(f"Order {oid} marked as processed")

def escalate(oid: str, reason: str):
    st.session_state.orders[oid]["status"] = "Escalated"
    note = st.session_state.orders[oid].get("notes", "")
    st.session_state.orders[oid]["notes"] = (note + f"\n[ESCALATED {datetime.now().strftime('%Y-%m-%d %H:%M')}] {reason}").strip()
    st.toast(f"Order {oid} reported to supervisor")

def filtered_orders():
    q = st.session_state.get("q", "").strip().lower()
    status = st.session_state.get("status_filter", "All")
    vip_only = st.session_state.get("vip_only", False)

    items = list(st.session_state.orders.items())
    if q:
        items = [(k, v) for k, v in items if q in v["customer"].lower() or q in v["tel"].replace(" ", "")]
    if status != "All":
        items = [(k, v) for k, v in items if v["status"] == status]
    if vip_only:
        items = [(k, v) for k, v in items if v["vip"]]
    return items

# -------------------- Header meta -------------------
processed_today = sum(1 for _, o in st.session_state.orders.items() if o["processed_on"] == date.today())
remains = sum(1 for _, o in st.session_state.orders.items() if o["status"] != "Processed")

st.caption(f"Processed today: {processed_today}")
st.caption(f"Remains: {remains}")

# Rep card (top-right like the mock)
hdr_l, hdr_r = st.columns([3, 1])
with hdr_r:
    with st.container(border=True):
        st.write("Craig")
        st.caption("ID: 003224")

# -------------------- Filters / actions -------------
with st.container(border=True):
    c1, c2, c3, c4 = st.columns([2, 1.3, 1, 1])
    with c1:
        st.text_input("Search (name or phone)", key="q", placeholder="e.g. Eric or 323...")
    with c2:
        st.selectbox("Status", ["All"] + STATUSES, key="status_filter", index=0)
    with c3:
        st.toggle("VIP only", key="vip_only")
    with c4:
        if st.button("Clear filters"):
            st.session_state.q = ""
            st.session_state.status_filter = "All"
            st.session_state.vip_only = False

st.divider()

# -------------------- Orders list -------------------
orders_to_show = filtered_orders()
if not orders_to_show:
    st.info("No orders match the current filters.")

for oid, o in orders_to_show:
    with st.container(border=True):
        top = st.columns([1, 2.3, 2.3, 1.2])
        # Left — name & actions
        with top[0]:
            st.write(f"**{o['customer']}**")
            # Escalation form (inline)
            with st.expander("Report to Supervisor"):
                reason = st.text_area("Reason", key=f"reason_{oid}", placeholder="Describe the issue…")
                if st.button("Submit report", key=f"submit_report_{oid}"):
                    escalate(oid, reason or "(no reason given)")
            if st.button("Mark As Processed", type="primary", key=f"proc_{oid}"):
                mark_processed(oid)

        # Row 1 boxes
        with top[1]:
            info_box("Subtotal", f"${o['subtotal']}")
        with top[2]:
            # Tel + call button
            with st.container(border=True):
                st.write("**Tel:**", o["tel"])
                # Use tel: so on mobile it opens dialer (Streamlit-only widget)
                st.link_button("Call", f"tel:{o['tel'].replace(' ', '')}", use_container_width=True)
        with top[3]:
            info_box("Ordertime", str(o["order_times"]))

        # Row 2 boxes
        btm = st.columns([2.3, 2.3, 1.2, 1])
        with btm[0]:
            with st.container(border=True):
                st.write(f"**Position:** {o['position']}")
                if st.button("Detail", key=f"detail_{oid}"):
                    st.session_state.detail_order_id = oid
        with btm[1]:
            info_box("Duration", f"{o['duration_days']} days")
        with btm[2]:
            info_box("VIP", "YES" if o["vip"] else "NO")
        with btm[3]:
            # Status quick-switch
            new_status = st.selectbox("Status", STATUSES, index=STATUSES.index(o["status"]), key=f"status_{oid}")
            if new_status != o["status"]:
                o["status"] = new_status
                st.toast(f"{oid} → {new_status}")

# -------------------- Detail / notes panel ----------
st.divider()
with st.container(border=True):
    st.write("**Detail / Follow-up**")
    oid = st.session_state.detail_order_id
    if not oid:
        st.caption("Select **Detail** on an order to edit notes and schedule follow-up.")
    else:
        o = st.session_state.orders[oid]
        st.write(f"Order **{oid}** — **{o['customer']}**  |  Phone: {o['tel']}  |  Subtotal: ${o['subtotal']}")
        # Notes
        st.text_area("Notes", key=f"notes_{oid}", value=o.get("notes", ""), height=120)
        # Follow-up scheduling (local-only placeholder)
        colf1, colf2, colf3 = st.columns([1, 1, 1])
        with colf1:
            f_date = st.date_input("Follow-up date", value=date.today())
        with colf2:
            f_time = st.time_input("Follow-up time", value=time(10, 0))
        with colf3:
            if st.button("Save updates", type="primary"):
                st.session_state.orders[oid]["notes"] = st.session_state[f"notes_{oid}"].strip()
                st.toast("Updates saved")
        st.caption("(Integrate with your CRM or notifications for real reminders.)")

# -------------------- Footer snapshot ----------
st.divider()
m1, m2, m3 = st.columns(3)
m1.metric("Processed today", processed_today)
m2.metric("Total open", remains)
m3.metric("VIPs in queue", sum(1 for _, o in st.session_state.orders.items() if o["vip"] and o["status"] != "Processed"))