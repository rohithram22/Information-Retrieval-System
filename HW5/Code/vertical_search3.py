from urllib.parse import urlparse
import streamlit as st
from elasticsearch7 import Elasticsearch
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
nltk.download('punkt')

# Function to highlight text hits with reduced opacity
def highlight_text(text, query):
    words = word_tokenize(query.lower())
    highlighted_text = text
    for word in words:
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        highlighted_text = pattern.sub(r'<span style="background-color: rgba(255, 255, 0, 0.5);">\g<0></span>', highlighted_text)
    return highlighted_text

# Function to read query-data file
def read_query_data():
    try:
        with open("qrels.txt", "r") as f:
            query_data = f.readlines()
    except FileNotFoundError:
        query_data = []
    return query_data

# Function to write query-data to file
def write_query_data(query_data):
    with open("qrels.txt", "w") as f:
        f.writelines(query_data)

# Function to get the current grade for an article
def get_current_grade(query_id, assessor_id, article_id, query_data):
    for line in query_data:
        data = line.strip().split()
        if len(data) == 4 and data[0] == query_id and data[1] == assessor_id and data[2] == article_id:
            return int(data[3])
    return None

# Function to update the grade for an article in the query-data file
def update_grade_in_query_data(query_id, assessor_id, article_id, grade, query_data):
    updated_query_data = []
    for line in query_data:
        data = line.strip().split()
        if len(data) == 4 and data[0] == query_id and data[1] == assessor_id and data[2] == article_id:
            updated_query_data.append(f"{query_id} {assessor_id} {article_id} {grade}\n")
        else:
            updated_query_data.append(line)
    return updated_query_data

# Function to perform Elasticsearch search
def perform_search(text_query):
    INDEX = 'crawler'
    es = Elasticsearch(cloud_id= "6200:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyRiZTllZjE5NDRkNTg0MDE3YTU0NDg0MzcwYjk5MjQzMSQ2Zjg1ODJhNWRjMGY0NDBhODU1Njk1MDQ4NzMyNmU2Yg==",
                       http_auth=("elastic",'fwOhKti7myB3PKFHQavQBhcr'))
    response = es.search(
        index=INDEX,
        body={
        "query": {
            "multi_match": {
            "query": text_query,
            "fields": ["title", "content"]
            }
        }
        }, size=250
    )
    display_list = {}
    for hit in response['hits']['hits']:
        display_list[hit["_id"]] = {
            "content": hit["_source"]["content"],
            "author": hit["_source"]["author"],
            "title": hit["_source"]["title"]
        }
    return display_list

# Function to get the count of assessed documents for each query ID
def get_query_assessed_count(query_data):
    query_assessed_count = {}
    for line in query_data:
        data = line.strip().split()
        if len(data) == 4:
            query_id = data[0]
            if query_id not in query_assessed_count:
                query_assessed_count[query_id] = 0
            query_assessed_count[query_id] += 1
    return query_assessed_count

# Streamlit app
def main():
    st.title("Vertical Search Page HW5")
    # User input
    text_query = st.text_input("Enter your Query", key="text_query")
    query_id = st.text_input("Enter Query ID", key="query_id")
    assessor_id = st.text_input("Enter Assessor ID", key="assessor_id")

    if 'display_list' not in st.session_state:
        st.session_state.display_list = {}

    if 'assessed_count' not in st.session_state:
        st.session_state.assessed_count = 0

    if st.button("Search"):
        st.session_state.display_list = perform_search(text_query)
        st.session_state.assessed_count = 0  # Reset assessed count on new search
    
    query_data = read_query_data()
    query_assessed_count = get_query_assessed_count(query_data)
    
    # Display search results with improved design
    if st.session_state.display_list:
        for article_id, article_info in st.session_state.display_list.items():
            with st.expander(f"**URL:** {article_id}"):
                st.markdown(f"# {article_info['title'].strip()}")
                st.markdown(f"**Author:** {','.join(article_info['author'])}")
                highlighted_content = highlight_text(article_info['content'], text_query)
                st.markdown(highlighted_content, unsafe_allow_html=True)
                current_grade = get_current_grade(query_id, assessor_id, article_id, query_data)
                if current_grade is not None:
                    relevance = {0: "non-relevant", 1: "relevant", 2: "very relevant"}[current_grade]
                else:
                    relevance = "non-relevant"
                relevance = st.radio(f"Relevance", ("non-relevant", "relevant", "very relevant"), index={"non-relevant": 0, "relevant": 1, "very relevant": 2}[relevance], key=f"relevance_{article_id}")
                grade = {"non-relevant": 0, "relevant": 1, "very relevant": 2}[relevance]
                if st.button("Update", key=f"update_{article_id}"):
                    if current_grade is None:
                        query_data.append(f"{query_id} {assessor_id} {article_id} {grade}\n")
                        st.session_state.assessed_count += 1
                        if query_id not in query_assessed_count:
                            query_assessed_count[query_id] = 0
                        query_assessed_count[query_id] += 1
                    else:
                        query_data = update_grade_in_query_data(query_id, assessor_id, article_id, grade, query_data)
                    write_query_data(query_data)
                    st.success(f"Assessment updated.")
    else:
        st.write("No results found.")
    
    st.sidebar.markdown(f"**Number of Assessed Documents:** {st.session_state.assessed_count}")
    for query_id, count in query_assessed_count.items():
        st.sidebar.markdown(f"**Assessed Documents for Query {query_id}:** {count}")

if __name__ == "__main__":
    main()