import streamlit as st
import gap_assessment

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Gap Assessment"])

if page == "Gap Assessment":
    gap_assessment.run()
    st.stop()

st.title("Dashboard")
st.write("Welcome to the Product Metadata Management App!")