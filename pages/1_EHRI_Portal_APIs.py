import streamlit as st
import requests as r
import json
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
import numpy as np

st.title('EHRI Portal APIs')

# A variable to keep track of which page we're on for the DocUnits
if "pageNumber" not in st.session_state:
    st.session_state['pageNumber'] = 1
if "data" not in st.session_state:
    st.session_state['data'] = []
if "countries" not in st.session_state:
    st.session_state['countries'] = {}
if "repos" not in st.session_state:
    st.session_state['repos'] = []
if "country" not in st.session_state:
    st.session_state['country'] = ""
if "query" not in st.session_state:
    st.session_state['query'] = ""
if "searchResults" not in st.session_state:
    st.session_state['searchResults'] = []


# We use a GraphQL query to get the names and ISO-2 codes of all
# the countries for which EHRI has a country report and we create
# a dictionary with the names of the countries as keys and their
# ISO-2 codes as values.

GraphQLEndpoint = 'https://portal.ehri-project-stage.eu/api/graphql'

@st.experimental_memo
def get_EHRI_countries():
    countries_query = """
    query Countries {
      countries{
        items {
          identifier
          name
        }
      }
    }
    """
    # headers={"X-Stream": "true"} is used to deactivate pagination
    res = r.post(GraphQLEndpoint, headers={"X-Stream": "true"}, json={'query': countries_query})
    res_json = json.loads(res.text)
    res_data = res_json['data']['countries']['items']
    for i in res_data:
        st.session_state['countries'][i['name']] = i['identifier']
    return st.session_state['countries']

countries = get_EHRI_countries()

def change_search_term(new, countrychange):
    st.session_state['query'] = new
    if countrychange:
        st.session_state['pageNumber'] = 1
    else:
        pass

with st.sidebar:
    with st.form("my_country"):
        st.session_state['country'] = st.selectbox("Country", sorted(list(countries.keys())))
        st.form_submit_button("Submit", on_click=change_search_term, args=("",True))

def fetch(url):
    try:
        result = r.get(url)
        return result.json()
    except AttributeError:
        st.write(AttributeError)


@st.experimental_memo
def get_repos_in_country(id):
    repos = []
    code = '"%s"' % id
    repos_per_country_query = """
query Country {
  Country(id: %s) {
	id
    identifier
    name
    itemCount
    repositories {
      items {
        id
        type
        identifier
        descriptions
        {
          languageCode
          name
        }
        latitude
        longitude
        itemCount
        documentaryUnits(all: true) {
          items {
            id
            type
            identifier
            descriptions {
              languageCode
              name
            }
          }
        }
      }
    }
  }
}
    """ % code
    # headers={"X-Stream": "true"} is used to deactivate pagination
    res = r.post(GraphQLEndpoint, headers={"X-Stream": "true"}, json={'query': repos_per_country_query})
    res_json = json.loads(res.text)
    repos.extend(res_json['data']['Country']['repositories']['items'])
    return repos


def get_country_data():
    st.session_state['repos'] = []
    r = fetch(f"https://portal.ehri-project.eu/api/v1/{countries[st.session_state['country']].lower()}")
    return r


def next_page():
    st.session_state['pageNumber'] += 1

def prev_page():
    st.session_state['pageNumber'] -= 1

try:
    st.session_state['data'] = get_country_data()
except KeyError:
    st.error(f"There is no EHRI country report for {st.session_state['country']}.")

data = st.session_state['data']

st.header(data['data']['attributes']['name'])
tab1, tab2, tab3 = st.tabs(["Country Report", "Archival Institutions", f"Search within {st.session_state['country']}"])
with tab1:
    if data['data']['attributes']['history']:
        st.subheader("History")
        st.write(data['data']['attributes']['history'])
    if data['data']['attributes']['situation']:
        st.subheader("Archival Situation")
        st.write(data['data']['attributes']['situation'])
    if data['data']['attributes']['summary']:
        st.subheader("EHRI Research (Summary)")
        st.write(data['data']['attributes']['summary'])
    if data['data']['meta']['subitems']:
        st.subheader("Number of Institutions Listed")
        st.text(data['data']['meta']['subitems'])
with tab2:
    with st.spinner('Please wait while we collect data...'):
        st.session_state['repos'] = get_repos_in_country(countries[st.session_state['country']].lower())
        try:
            if len(st.session_state['repos']):
                df = pd.json_normalize(st.session_state['repos'], "descriptions",
                                       ["id", "latitude", "longitude", "itemCount"])
                no_nan_df = df.dropna(axis=0)
                # Define a layer to display on a map
                if not no_nan_df.empty:
                    st.subheader("Map")
                    layer = pdk.Layer(
                        "ScatterplotLayer",
                        no_nan_df,
                        get_position=["longitude", "latitude"],
                        get_FillColor='[200, 30, 0, 160]',
                        get_radius=100,
                        pickable=True,
                        radius_scale=1,
                        radius_min_pixels=3,
                        radius_max_pixels=5,
                    )
                    # Set the viewport location
                    view_state = pdk.ViewState(latitude=no_nan_df.iloc[0]['latitude'],
                                               longitude=no_nan_df.iloc[0]['longitude'], zoom=2, )
                    st.pydeck_chart(pdk.Deck(map_style=None, initial_view_state=view_state, layers=layer,
                                             tooltip={"text": "{name}"}))
                st.subheader("List")
                for (n, i) in enumerate(st.session_state['repos']):
                    st.write(str(n + 1) + ". " + i["descriptions"][0]["name"])
                    st.markdown(f"[EHRI Portal Link](https://portal.ehri-project.eu/institutions/{i['id']})", unsafe_allow_html=True)
        except KeyError:
            st.error(f"There is no EHRI country report for {st.session_state['country']}.")
with tab3:
    search_input = st.text_input(f"Search for Archival Descriptions in {st.session_state['country']}", key="search_input")

    if search_input:
        change_search_term(search_input, False)

    st.session_state['searchResults'] = fetch(
        f"https://portal.ehri-project.eu/api/v1/search?&facet=type&facet=holder&facet=country&facet=lang&q={st.session_state['query']}&country={countries[st.session_state['country']].lower()}&type=DocumentaryUnit&page={st.session_state['pageNumber']}")

    if st.session_state['searchResults']['meta']['pages'] == 1 and st.session_state['pageNumber']!=1:
        st.session_state['pageNumber']=1
        st.session_state['searchResults'] = fetch(
            f"https://portal.ehri-project.eu/api/v1/search?&facet=type&facet=holder&facet=country&facet=lang&q={st.session_state['query']}&country={countries[st.session_state['country']].lower()}&type=DocumentaryUnit&page={st.session_state['pageNumber']}")


    if st.session_state['searchResults']:
        doc_units = st.session_state['searchResults']['data']
        if len(doc_units):
            for i in st.session_state['searchResults']['meta']['facets']:
                if i['param'] == "holder":
                    holders = i['facets']

            def pie_plt():
                plt.subplots(figsize=(8, 8), subplot_kw=dict(aspect="equal"))
                # Pie Chart
                plt.pie([x['count'] for x in holders if x['count']!=0],
                        labels=[f"{x['name']}: {x['count']}" for x in holders if x['count']!=0],
                        pctdistance=0.85,wedgeprops=dict(width=0.5), startangle=-40
                    )

                # Adding Title of chart
                plt.title('Archival Descriptions per Institution')
                return st.pyplot(plt)

            col1, col2 = st.columns(2)

            col1.metric("Archival Descriptions matching you search", st.session_state['searchResults']['meta']['total'])
            col2.metric("Holding Institutions matching you search", len(holders))

            pie_plt()

            st.write(f"Displaying results for \"{st.session_state['query']}\"")

            st.subheader("Archival Descriptions")
            for i in doc_units:
                st.write("* "+f"[{i['attributes']['descriptions'][0]['name']}](https://portal.ehri-project.eu/units/{i['id']})")

            col3, col4, col5 = st.columns(3)

            if "prev" in st.session_state['searchResults']['links']:
                col3.button("Previous Page", on_click=prev_page)
            with col4:
                st.write("Page " + str(st.session_state['pageNumber']) + " of " + str(st.session_state['searchResults']['meta']['pages']))
            if "next" in st.session_state['searchResults']['links']:
                col5.button("Next Page", on_click=next_page)

        elif len(search_input) == 0 and st.session_state['searchResults']['meta']['total'] == 0:
            st.error(f"Sorry. There are no archival descriptions linked to {st.session_state['country']}")

        else:
            st.error(
                f"Sorry. We couldn't find any archival descriptions regarding your search term in {st.session_state['country']}. Try again with another term.")
