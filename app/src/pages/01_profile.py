# pages/Account.py
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(page_title="Account", layout="wide")

SideBarLinks()

st.title('Your Profile')

if "profile" not in st.session_state:
    st.session_state.profile = {
        "username": "Eric.C",
        "company": "Florida Nuts INC.",
        "phone": "(323) 748-2748",
        "email": "eric.c@gmail.com",
        "industry": "Food Manufacturing",
        "position": "Founder/CEO",
        "avatar_url": "https://i.pravatar.cc/200?img=13",
    }

# Track per-field edit modes
for k in ["company", "phone", "email", "industry", "position"]:
    st.session_state.setdefault(f"edit_{k}", False)

left, right = st.columns([1, 2])

def row(label, value):
    data, modify = st.columns([3, 1])
    with data:
        with st.container(gap=None):
            st.write(f"**{value}**")
            st.caption(label)
    with modify:
        if st.button("✏️", key=f"edit_{label}", type="secondary", use_container_width=True):
            st.toast(f"Editing {label}")

with left:
    with st.container(border=True, gap=None):
        ac, bc, cc = st.columns([1, 2, 1])
        with bc:
            st.image("https://i.pravatar.cc/200?img=13", width=120, caption="")
        st.divider()

        st.caption("Username")
        st.write("**Eric.C**")
        st.divider()

        # Editable fields
        row("Company", "Florida Nuts INC.")
        row("Tel Number", "(323) 748-2748")
        row("Email", "eric.c@gmail.com")
        st.divider()
        row("Industry", "Food Manufacturing")
        row("Position", "Founder/CEO")

# ================= Right: Accordions =========================================
with right:
    with st.expander("My Orders", expanded=True):
        st.info("You don't have any order yet!")
        st.button("Browse products", type="primary")

    with st.expander("Privacy Setting", expanded=False):
        st.checkbox("Show my email to teammates", value=True)
        st.checkbox("Enable two-factor authentication", value=False)
        st.checkbox("Allow analytics & diagnostics", value=True)
        st.button("Save privacy settings", type="primary")

    with st.expander("My Balance", expanded=False):
        bal_l, bal_r = st.columns([2, 1])
        with bal_l:
            st.metric("Current Balance", "$0.00")
        with bal_r:
            st.button("Add Funds", type="primary", use_container_width=True)
        st.caption("Balance updates after successful payment settlement.")

    with st.expander("Manage Payment Method", expanded=False):
        st.write("No saved cards.")
        add_c1, add_c2 = st.columns(2)
        with add_c1:
            st.text_input("Cardholder name", placeholder="Name on card")
        with add_c2:
            st.text_input("Card number", placeholder="xxxx xxxx xxxx xxxx")
        c3, c4, c5 = st.columns([1, 1, 1])
        with c3:
            st.text_input("MM/YY", placeholder="MM/YY")
        with c4:
            st.text_input("CVC", placeholder="CVC")
        with c5:
            st.button("Add Card", type="primary", use_container_width=True)

    with st.expander("Feedbacks", expanded=False):
        fb = st.text_area("Leave your feedback", placeholder="Tell us what we can improve…")
        cols = st.columns([1, 1])
        if cols[0].button("Submit Feedback", type="primary"):
            st.toast("Thanks for the feedback!")
        if cols[1].button("Clear"):
            st.session_state["Feedbacks-Leave your feedback"] = ""
