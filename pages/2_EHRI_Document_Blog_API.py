import streamlit as st
import requests as r
import re

if "country" not in st.session_state:
    st.session_state['country'] = ""
if "posts" not in st.session_state:
    st.session_state['posts'] = ""
if "WP-Res" not in st.session_state:
    st.session_state['WP-Res'] = ""
if "total-pages" not in st.session_state:
    st.session_state['total-pages'] = ""
if "db-page" not in st.session_state:
    st.session_state['db-page'] = 1
if "db-query" not in st.session_state:
    st.session_state['db-query'] = ""

def get_posts(query="", page=1):
    results = r.get("https://blog.ehri-project.eu/wp-json/wp/v2/search?",
              params= {
                'type': 'post',
                'per_page': 6,
                'search': query,
                '_embed': 'true',
                'page': page,
              })
    st.session_state['WP-Res'] = results
    st.session_state['posts'] = st.session_state['WP-Res'].json()
    st.session_state['total'] = st.session_state['WP-Res'].headers['X-WP-Total']
    st.session_state['total-pages'] = st.session_state['WP-Res'].headers['X-WP-TotalPages']

def next_page():
    st.session_state['db-page'] += 1

def prev_page():
    st.session_state['db-page'] -= 1

def get_post_thumbnail(id):
    result = r.get(f"https://blog.ehri-project.eu/wp-json/wp/v2/media/{id}")
    return result.json()['media_details']['sizes']['medium']['source_url']

def change_search_term(new):
    st.session_state['db-query'] = new

st.title('EHRI Document Blog API (Wordpress REST API)')

with st.form(key='search_DB'):
    search_input = st.text_input(f"Search for posts", key="search_input")
    submit_button = st.form_submit_button(label='Submit')

if submit_button:
    st.session_state['db-page'] =1
    change_search_term(search_input)

st.subheader('Posts')

get_posts(st.session_state['db-query'],st.session_state['db-page'])



# DB_input = st.text_input(f"Most ", key="search_input")
col4,col5,col6 = st.columns(3)
with col4:
    pass
with col5:
    for post in st.session_state['posts']:
        thumb = get_post_thumbnail(post['_embedded']['self'][0]['featured_media'])
        with st.container():
            st.image(thumb, width=200,)
            # Using regex to get rid of html tags such as <strong> within post titles
            st.markdown(f"[{re.sub('<[^<]+?>', '', post['title'])}]({post['url']})", unsafe_allow_html=True)
with col6:
    pass

col1,col2,col3 = st.columns(3)

if st.session_state['db-page'] > 1:
    with col1:
        st.button("Previous", on_click=prev_page)
with col2:
    st.write(f"Page {st.session_state['db-page']} of {st.session_state['total-pages']}")
if int(st.session_state['db-page']) < int(st.session_state['total-pages']):
    with col3:
        st.button("Next", on_click=next_page)