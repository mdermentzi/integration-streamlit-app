import streamlit as st

st.set_page_config(
    page_title='EHRI Integration Workshop',
)

st.title('EHRI Integration Workshop')

st.markdown(
    """
    Welcome to the EHRI Integration Workshop. In today's workshop, we'll review the <a href='/EHRI_Portal_APIs' target='_self'>EHRI Portal APIs (Search & GraphQL)</a>, 
    as well as the <a href="/EHRI_Document_Blog_API" target="_self">Document Blog API (Wordpress REST)</a>. We will also be looking into
    how to use geodata served through the <a href="/EHRI_Geodata" target="_self">EHRI Geodata repository</a> within apps and map visualisations hosted elsewhere.
     """, unsafe_allow_html=True)