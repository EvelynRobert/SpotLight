import streamlit as st
from modules.nav import SideBarLinks
import requests
import json

SideBarLinks()

st.title('O&M Dashboard')

API_URL = "http://web-api:4000/o_and_m"
st.session_state.setdefault("search_results", None)
st.session_state.setdefault("full_db_search", "")
st.session_state.setdefault("enter_data_db", "")

def performSearch(query):
    try:
        response = requests.get(f"{API_URL}/search", params={"query": query})
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Error fetching search results")
            return []
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []

col_left1, col_right1 = st.columns(2)
with col_left1:
    with st.container():
        st.text_input("**Full DB Search**", placeholder="Enter query here", key="full_db_search")

        clear_column, search_column = st.columns(2)
        with clear_column:
            if st.button("Clear Search", type='secondary', use_container_width=True):
                st.session_state.full_db_search = ""
                st.session_state.search_results = None
                st.toast("Search cleared")
                st.rerun()

        with search_column:
            if st.button("Search DB", type='primary', use_container_width=True):
                query = (st.session_state.get("full_db_search") or "").strip()
                if not query:
                    st.warning("Please enter a search query.")
                else:
                    st.toast("Performing search...")
                    with st.spinner("Searching..."):
                        data = performSearch(query)

                    # normalize result to a dict with expected keys
                    if isinstance(data, dict):
                        spots = data.get("spots", [])
                        customers = data.get("customers", [])
                        orders = data.get("orders", [])
                        st.session_state.search_results = {
                            "spots": spots, "customers": customers, "orders": orders
                        }
                    else:
                        st.session_state.search_results = {"spots": [], "customers": [], "orders": []}

        with st.container(border=True):
            st.write("**Search Results**")

            results = st.session_state.search_results
            if not results:
                st.caption("No search performed yet. Enter a query and click **Search DB**.")
            else:
                tabs = st.tabs([
                    f"Spots ({len(results['spots'])})",
                    f"Customers ({len(results['customers'])})",
                    f"Orders ({len(results['orders'])})",
                ])

                with tabs[0]:
                    if results["spots"]:
                        st.dataframe(results["spots"], use_container_width=True)
                    else:
                        st.caption("No spots found.")

                with tabs[1]:
                    if results["customers"]:
                        st.dataframe(results["customers"], use_container_width=True)
                    else:
                        st.caption("No customers found.")

                with tabs[2]:
                    if results["orders"]:
                        st.dataframe(results["orders"], use_container_width=True)
                    else:
                        st.caption("No orders found.")

with col_right1:
    with st.container():
        st.text_input("**Insert Data into DB**", placeholder="Enter query here", key="enter_data_db")

        clear_column, insert_column = st.columns(2)
        with clear_column:
            if st.button("Clear Data", type='secondary', use_container_width=True):
                st.session_state.enter_data_db = ""
                st.toast("Data cleared")

        with insert_column:
            if st.button("Insert Data", type='primary', use_container_width=True):
                st.toast("Performing insert...")
                try:
                    payload = json.loads(st.session_state.enter_data_db)
                    r = requests.post(f"{API_URL}/insert", json=payload)
                    if r.status_code in (200, 201):
                        st.success("Insert successful")
                        st.json(r.json())
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")
                except json.JSONDecodeError:
                    st.error("Invalid JSON")
                except Exception as e:
                    st.error(f"Request failed: {e}")

        with st.container(border=True):
            st.write("**Preview**")
            if st.session_state.enter_data_db.strip():
                try:
                    st.json(json.loads(st.session_state.enter_data_db))
                except:
                    st.write("Invalid JSON. Cannot preview.")
            else:
                st.caption("No data to preview. Please enter data and click **Insert Data** to see a preview here.")

st.divider()

d1, d2, d3 = st.columns(3)
with d1:
    with st.container():
        spot_id = st.text_input("**Delete Spot by ID**", placeholder="Enter ID", key="delete_spot_id")
        if st.button("Delete", type='primary', use_container_width=True, key="delete_spot"):
            if spot_id.strip():
                try:
                    r = requests.delete(f"{API_URL}/spot/{spot_id}")
                    if r.status_code == 200:
                        st.success(f"Spot {spot_id} deleted")
                        st.json(r.json())
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")
            else:
                st.warning("Please enter a Spot ID.")

with d2:
    with st.container():
        customer_id = st.text_input("**Delete Customer by ID**", placeholder="Enter ID", key="delete_customer_id")
        if st.button("Delete", type='primary', use_container_width=True, key="delete_customer"):
            if customer_id.strip():
                try:
                    r = requests.delete(f"{API_URL}/customer/{customer_id}")
                    if r.status_code == 200:
                        st.success(f"Customer {customer_id} deleted")
                        st.json(r.json())
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")
            else:
                st.warning("Please enter a Customer ID.")

with d3:
    with st.container():
        order_id = st.text_input("**Delete Order by ID**", placeholder="Enter ID", key="delete_order_id")
        if st.button("Delete", type='primary', use_container_width=True, key="delete_order"):
            if order_id.strip():
                try:
                    r = requests.delete(f"{API_URL}/order/{order_id}")
                    if r.status_code == 200:
                        st.success(f"Order {order_id} deleted")
                        st.json(r.json())
                    else:
                        st.error(f"Error {r.status_code}: {r.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")
            else:
                st.warning("Please enter an Order ID.")

st.divider()

col_left2, col_right2 = st.columns(2)
with col_left2:
    with st.container(border=True):
        with st.container(gap=None):
            st.write('## TODO List')
            st.write("**Current: 2**")

        with st.container(border=True, gap="small"):
            with st.container(gap=None):
                st.write("**Subject:** Invalid Spot Information")
                st.caption("**Reporter:** Craig #003224")
                st.caption("2914 NE 13th Dr Gainesville")

            st.image("https://bloximages.newyork1.vip.townnews.com/kq2.com/content/tncms/assets/v3/editorial/9/30/9304a95a-99cb-11ee-9aaf-8fda7d79b88c/6579cc9dbaf31.image.jpg")

            with st.container(gap="small"):
                if st.button("Set subject as 'w.issue'",
                             type='primary', use_container_width=True, key="wissue1"):
                    st.toast("Marked as issue")
                if st.button("Remove from DB",
                             type='primary', use_container_width=True, key="remove1"):
                    st.toast("Removed from DB")
                if st.button("Revoke this report",
                             type='primary', use_container_width=True, key="revoke1"):
                    st.toast("Revoked")

        with st.container(border=True, gap="small"):
            with st.container(gap=None):
                st.write("**Subject:** New employee acquiring account authorization")
                st.caption("**Name:** Kyle")
                st.caption("**Position:** Sales")

            st.image("https://preview.redd.it/pd70boo4s2u71.jpg?auto=webp&s=322e6e589b15a8898de5b5ef82fe35542a5d3840")

            with st.container(gap="small"):
                if st.button("Authorize",
                             type='primary', use_container_width=True, key="authorize1"):
                    st.toast("Authorized Kyle")
                if st.button("Reject",
                             type='primary', use_container_width=True, key="reject1"):
                    st.toast("Rejected Kyle's authorization")

with col_right2:
    with st.container(border=True):
        st.write("**Spots Info:**")
        try:
            r = requests.get(f"{API_URL}/spots/metrics")
            if r.status_code == 200:
                data = r.json()
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total", data["total"])
                m2.metric("In-use", data["in_use"])
                m3.metric("Free", data["free"])
                m4.metric("W.Issue", data["with_issue"])
            else:
                st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Failed to fetch spots metrics: {e}")

        if st.button("Print details", use_container_width=True, key="print_spots"):
            try:
                r = requests.get(f"{API_URL}/spots/summary?limit=10")
                if r.status_code == 200:
                    st.json(r.json())
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Failed to fetch spot details: {e}")

    with st.container(border=True):
        st.write("**Customers Account Info:**")
        try:
            r = requests.get(f"{API_URL}/customers/metrics")
            if r.status_code == 200:
                data = r.json()
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total", data["total"])
                c2.metric("VIP", data["vip"])
                c3.metric("Never Ordered", data["never_ordered"])
                c4.metric("Avg Order Time", data["avg_order_time"])
            else:
                st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Failed to fetch customers metrics: {e}")

        if st.button("Print details", use_container_width=True, key="print_customers"):
            try:
                r = requests.get(f"{API_URL}/customers/summary?limit=10")
                if r.status_code == 200:
                    st.json(r.json())
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Failed to fetch customer details: {e}")

    with st.container(border=True):
        st.write("**Order Info:**")
        try:
            r = requests.get(f"{API_URL}/orders/metrics", params={"period": "90d"})
            if r.status_code == 200:
                data = r.json()
                o1, o2, o3 = st.columns(3)
                o1.metric("Total", data["total"])
                o2.metric("Avg price", f"${data['avg_price']}")
                o3.metric("Last 90 days", data["last_period"])
            else:
                st.error(f"Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Failed to fetch orders metrics: {e}")

        if st.button("Print details", use_container_width=True, key="print_orders"):
            try:
                r = requests.get(f"{API_URL}/orders/summary?period=90d&limit=10")
                if r.status_code == 200:
                    st.json(r.json())
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Failed to fetch order details: {e}")