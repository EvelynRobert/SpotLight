import streamlit as st
from streamlit_extras.app_logo import add_logo
from modules.nav import SideBarLinks

SideBarLinks()

st.set_page_config(layout = 'wide')

st.title("O&M Dashboard")

col1, col2 = st.columns([1, 3])
with col1:
    with st.container(border=True):
        st.write("**TODO List**")
        st.write("Current: " + "2")