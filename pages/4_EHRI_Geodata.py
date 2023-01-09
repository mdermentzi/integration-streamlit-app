import streamlit as st
import leafmap.foliumap as leafmap
import ast

st.set_page_config(layout="wide")

# Credit to https://github.com/giswqs/streamlit-geospatial/blob/master/pages/7_%F0%9F%93%A6_Web_Map_Service.py

# pip install leafmap and OWSLib
@st.cache
def get_layers(url):
    options = leafmap.get_wms_layers(url)
    return options


def app():
    st.title("Web Map Service (WMS)")

    row1_col1, row1_col2 = st.columns([3, 1.3])
    width = 800
    height = 600
    layers = None

    with row1_col2:

        ehri_geodata = "https://geodata.ehri-project.eu/geoserver/wms"
        empty = st.empty()
        options = get_layers(ehri_geodata)
        default = None


        layers = empty.multiselect(
            "Select WMS layers to add to the map:", options, default=default
        )
        add_legend = st.checkbox("Add a legend to the map", value=True)
        legend = ""
        if add_legend:
            legend_text = st.text_area(
                "Enter a legend as a dictionary {label: color}",
                value=legend,
                height=200,
            )

        with row1_col1:
            m = leafmap.Map(center=(36.3, 0), zoom=2)

            if layers is not None:
                for layer in layers:
                    m.add_wms_layer(
                        ehri_geodata, layers=layer, name=layer, attribution=" ", transparent=True
                    )
            if add_legend and legend_text:
                legend_dict = ast.literal_eval(legend_text)
                m.add_legend(legend_dict=legend_dict)

            m.to_streamlit(height=height)


app()