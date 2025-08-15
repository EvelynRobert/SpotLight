import streamlit as st
from modules.nav import SideBarLinks

SideBarLinks()

st.title('O&M Dashboard')

col_left1, col_right1 = st.columns(2)

with col_left1:
    with st.container():
        st.text_input("**Full DB Search**", placeholder="Enter query here", key="full_db_search")

        clear_column, search_column = st.columns(2)
        with clear_column:
            if st.button("Clear Search", type='secondary', use_container_width=True):
                st.toast("Search cleared")

        with search_column:
            if st.button("Search DB", type='primary', use_container_width=True):
                st.toast("Performing search...")

        with st.container(border=True):
            st.write("**Search Results**")
            st.write("No results found for your query.")
            # TODO: Implement search functionality to display results based on the query entered in the text input.

with col_right1:
    with st.container():
        st.text_input("**Insert Data into DB**", placeholder="Enter query here", key="enter_data_db")

        clear_column, insert_column = st.columns(2)
        with clear_column:
            if st.button("Clear Data", type='secondary', use_container_width=True):
                st.toast("Data cleared")

        with insert_column:
            if st.button("Insert Data", type='primary', use_container_width=True):
                st.toast("Performing insert...")

        with st.container(border=True):
            st.write("**Preview**")
            st.write("No data to preview. Please enter data to see a preview here.")
            # TODO: Preview functionality

st.divider()

d1, d2, d3 = st.columns(3)
with d1:
    with st.container():
        st.text_input("**Delete Spot by ID**", placeholder="Enter ID", key="delete_spot_id")
        if st.button("Delete", type='primary', use_container_width=True, key="delete_spot"):
            st.toast("Deleted")
with d2:
    with st.container():
        st.text_input("**Delete Customer by ID**", placeholder="Enter ID", key="delete_customer_id")
        if st.button("Delete", type='primary', use_container_width=True, key="delete_customer"):
            st.toast("Deleted")
with d3:
    with st.container():
        st.text_input("**Delete Order by ID**", placeholder="Enter ID", key="delete_order_id")
        if st.button("Delete", type='primary', use_container_width=True, key="delete_order"):
            st.toast("Deleted")

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
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", 1055)
        m2.metric("In-use", 840)
        m3.metric("Free", 133)
        m4.metric("W.Issue", 82)
        if st.button("Print details on Result Area", use_container_width=True, key="print_spots"):
            st.toast("Printing details on Result Area...")

    with st.container(border=True):
        st.write("**Customers Account Info:**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", 483)
        c2.metric("VIP", 21)
        c3.metric("Never Ordered", 139)
        c4.metric("Avg Order Time", "3")
        if st.button("Print details on Result Area", use_container_width=True, key="print_customers"):
            st.toast("Printing details on Result Area...")

    with st.container(border=True):
        st.write("**Order Info:**")
        o1, o2, o3 = st.columns(3)
        o1.metric("Total", 4855)
        o2.metric("Avg price", "$230")
        o3.metric("Last 90 days", 842)
        if st.button("Print details on Result Area", use_container_width=True, key="print_orders"):
            st.toast("Printing details on Result Area...")
