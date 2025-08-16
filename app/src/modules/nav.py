# Idea borrowed from https://github.com/fsmosca/sample-streamlit-authenticator

# This file has function to add certain functionality to the left side bar of the app

import streamlit as st

#### ------------------------ General ------------------------
def HomeNav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")

def CustomerPageNav():
    st.sidebar.page_link("pages/00_profile.py", label="Profile", icon="👤")
    st.sidebar.page_link("pages/01_customer_map.py", label="Customer Map", icon="🗺️")
    st.sidebar.page_link("pages/02_search.py", label="Search", icon="🔍")

def SalesmanPageNav():
    st.sidebar.page_link("pages/10_workbench.py", label="Workbench", icon="🔧")
    # st.sidebar.page_link("pages/02_Map_Demo.py", label="Map Demo", icon="🗺️")
    # st.sidebar.page_link("pages/03_World_Bank.py", label="World Bank Data", icon="🌍")
    # st.sidebar.page_link("pages/04_API_Testing.py", label="API Testing", icon="🔌")

def AdminPageNav():
    st.sidebar.page_link("pages/20_dashboard.py", label="O&M Dashboard", icon="🖥️")
    st.sidebar.page_link("pages/21_statistics.py", label="Statistics", icon="📊")
    st.sidebar.page_link("pages/22_management_map.py", label="Management Map", icon="🗺️")


# --------------------------------Links Function -----------------------------------------------
def SideBarLinks(show_home=False):

    # add a logo to the sidebar always
    st.sidebar.image("assets/logo.png", width=150)

    # If there is no logged in user, redirect to the Home (Landing) page
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        # Show the Home page link (the landing page)
        HomeNav()

    # Show the other page navigators depending on the users' role.
    if st.session_state["authenticated"]:

        # Show World Bank Link and Map Demo Link if the user is a political strategy advisor role.
        if st.session_state["role"] == "customer":
            CustomerPageNav()

        # If the user role is usaid worker, show the Api Testing page
        if st.session_state["role"] == "salesman":
            SalesmanPageNav()

        # If the user is an administrator, give them access to the administrator pages
        if st.session_state["role"] == "o&m":
            AdminPageNav()

    if st.session_state["authenticated"]:
        # Always show a logout button if there is a logged in user
        if st.sidebar.button("Logout"):
            del st.session_state["role"]
            del st.session_state["authenticated"]
            st.switch_page("Home.py")