import json

import streamlit as st
import pandas as pd
from datetime import datetime

from github import Github

# MUST be first command
st.set_page_config(layout="wide")

REPO_URL = "https://raw.githubusercontent.com/karendcl/fbio-web-requests/main/"
GITHUB_TOKEN = st.secrets["github_token"]  # Use Streamlit secrets in production
REPO_NAME = "karendcl/fbio-web-requests"  # Your repo
FILE_PATH = "data.json"  # Path to your JSON file
BRANCH = "main"  # Branch to update

def reqest_posted(row):
    """Update the status of the request to 'posted'.
    Remove the images from the github repository.
    """

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    # Get current JSON file
    file = repo.get_contents(FILE_PATH, ref=BRANCH)
    sha = file.sha
    current_data = json.loads(file.decoded_content.decode())

    # Update the status of the request
    for request in current_data:
        if request['timestamp'] == row['timestamp']:
            request['state'] = 'posted'
            break

    # Save the updated JSON file
    repo.update_file(
        path=FILE_PATH,
        message="Update request status to posted",
        content=json.dumps(current_data),
        sha=sha,
        branch=BRANCH
    )




# @st.cache_data(ttl=600)
def load_data():
    try:
        response = pd.read_json(REPO_URL + 'data.json')
        # Convert timestamp to datetime if it exists
        if 'timestamp' in response.columns:
            response['timestamp'] = pd.to_datetime(response['timestamp'])
        return response.to_dict('records')
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return []


def main():
    st.title("📊 Enhanced Request Dashboard")

    # Load data
    data = load_data()

    if not data:
        st.warning("No data found or couldn't load data.")
        return

    df = pd.DataFrame(data)

    # Sidebar filters and sorting
    with st.sidebar:
        st.header("Filters & Sorting")

        # Sorting options
        sort_options = {
            "Date (Newest First)": "timestamp_desc",
            "Date (Oldest First)": "timestamp_asc",
            "Name (A-Z)": "name_asc",
            "Name (Z-A)": "name_desc",
            "Status": "status"
        }
        selected_sort = st.selectbox(
            "Sort By",
            options=list(sort_options.keys()),
            index=0
        )

        # Status filter
        status_options = ["All"] + list(df['state'].unique())
        selected_status = st.selectbox(
            "Status",
            options=status_options,
            index=0
        )

        # Department filter
        department_options = ["All"] + list(df['department'].unique())
        selected_department = st.selectbox(
            "Department",
            options=department_options,
            index=0
        )

    # Apply filters
    filtered_df = df.copy()
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df['state'] == selected_status]
    if selected_department != "All":
        filtered_df = filtered_df[filtered_df['department'] == selected_department]

    # Apply sorting
    if sort_options[selected_sort] == "timestamp_desc":
        if 'timestamp' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('timestamp', ascending=False)
    elif sort_options[selected_sort] == "timestamp_asc":
        if 'timestamp' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('timestamp', ascending=True)
    elif sort_options[selected_sort] == "name_asc":
        filtered_df = filtered_df.sort_values('user_name', ascending=True)
    elif sort_options[selected_sort] == "name_desc":
        filtered_df = filtered_df.sort_values('user_name', ascending=False)
    elif sort_options[selected_sort] == "status":
        filtered_df = filtered_df.sort_values('state')

    # Display metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests", len(filtered_df))
    col2.metric("Pending", len(filtered_df[filtered_df['state'] == 'pending']))
    col3.metric("Completed", len(filtered_df[filtered_df['state'] == 'posted']))

    # Display data with action buttons
    for row_index, row in filtered_df.iterrows():
        with st.expander(f"{row.get('user_name', 'N/A')} - {row.get('state', 'N/A')} - "
                         f"{row.get('timestamp', '').strftime("%Y%m%d_%H%M%S") if pd.notna(row.get('timestamp')) else 'No Date'}",
                         expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("User Info")
                st.write(f"**Name:** {row.get('user_name', 'N/A')}")
                st.write(f"**Email:** {row.get('user_email', 'N/A')}")
                st.write(f"**Department:** {row.get('department', 'N/A')}")

            with col2:
                st.subheader("Request Info")
                st.write(f"**Topic:** {row.get('topic', 'N/A')}")
                st.write(f"**Message:** {row.get('message', 'N/A')}")

            if 'images' in row and row['images']:
                st.subheader(f"Attached Images ({len(row['images'])})")
                cols = st.columns(min(3, len(row['images'])))
                for i, img_url in enumerate(row['images']):
                    with cols[i % 3]:
                        path = REPO_URL + img_url
                        path = path.replace(' ', '%20')

                        st.markdown(f"[Download Image {i}]({path})", unsafe_allow_html=True)

            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Posted", key=f"approve_{row_index}"):








if __name__ == "__main__":
    main()