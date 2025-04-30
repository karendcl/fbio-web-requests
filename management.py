import json
import os

import streamlit as st
import pandas as pd
from datetime import datetime

from github import Github

from reports import get_statistics

# MUST be first command
st.set_page_config(layout="wide")

REPO_URL = "https://raw.githubusercontent.com/karendcl/fbio-web-requests/main/"
GITHUB_TOKEN = st.secrets["github_token"]  # Use Streamlit secrets in production
REPO_NAME = "karendcl/fbio-web-requests"  # Your repo
FILE_PATH = "data.json"  # Path to your JSON file
BRANCH = "main"  # Branch to update

def generate_email_content(row):
    """Generate email content for the request."""
    email_content = f"""
    Tema: Referente a su solicitud de publicación en la página web
    
    Estimado/a {row['user_name']},

    Su solicitud de publicación en la página web ha sido publicada. A continuación se detallan los datos de su solicitud:

    Nombre: {row['user_name']}
    Email: {row['user_email']}
    Departamento: {row['department']}
    Tema: {row['topic']}
    Mensaje: {row['message']}
    Cantidad de fotos recibidas: {len(row['images'])}
    Cantidad de archivos recibidos: {len(row['file'])}

    Gracias por su paciencia.
    Contacte a la administración si tiene alguna pregunta o inquietud.
    """
    return email_content

def request_posted(row):
    """Update the status of the request to 'posted'.
    """
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    # Get current JSON file
    file = repo.get_contents(FILE_PATH, ref=BRANCH)
    sha = file.sha
    current_data = json.loads(file.decoded_content.decode())

    # Update the status of the request
    for request in current_data:
        if request['user_name'] == row['user_name'] and \
                request['topic'] == row['topic'] and \
                request['department'] == row['department'] and \
                request['message'] == row['message']:
            request['state'] = 'posted'
            request['posted_timestamp'] = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save the updated JSON file
    repo.update_file(
        path=FILE_PATH,
        message="Update request status to posted",
        content=json.dumps(current_data, indent=4),
        sha=sha,
        branch=BRANCH
    )

def action_to_clean_images_and_files():
    """Clean up images and files from the request."""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    # Get current JSON file
    file = repo.get_contents(FILE_PATH, ref=BRANCH)
    sha = file.sha
    current_data = json.loads(file.decoded_content.decode())

    # Clean up images and files
    for request in current_data:
        if request['state'] == 'posted':
            for img_path in request['images']:
                try:
                    # Get the SHA of the file to delete
                    img_name1 = img_path[5:]
                    img_path = f"data/{img_name1}"
                    shai = repo.get_contents(img_path, ref=BRANCH).sha
                    repo.delete_file(
                        path=img_path,
                        message=f"Delete image {img_path}",
                        sha=shai,
                        branch=BRANCH
                    )
                except Exception as e:
                    print(f"Failed to delete image {img_path}: {str(e)}")
            for img_path in request['file']:
                try:
                    # Get the SHA of the file to delete
                    img_name1 = img_path[5:]
                    img_path = f"data/{img_name1}"
                    shai = repo.get_contents(img_path, ref=BRANCH).sha
                    repo.delete_file(
                        path=img_path,
                        message=f"Delete file {img_path}",
                        sha=shai,
                        branch=BRANCH
                    )
                except Exception as e:
                    print(f"Failed to delete file {img_path}: {str(e)}")


            request['images'] = []
            request['file'] = []

    # Save the updated JSON file
    repo.update_file(
        path=FILE_PATH,
        message="Clean up images and files",
        content=json.dumps(current_data, indent=4),
        sha=sha,
        branch=BRANCH
    )


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


def get_dataframe():
    # Load data
    data = load_data()

    if not data:
        st.warning("No data found or couldn't load data.")
        return

    df = pd.DataFrame(data)

    return df

def main():
    st.title("📊 Web Request Dashboard")

    df = get_dataframe()

    # Sidebar filters and sorting
    with st.sidebar:
        st.header("Filters & Sorting")

        # Sorting options
        sort_options = {
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

        st.divider()

        st.header("Actions")
        if st.button("Clean Up Images and Files", icon="🧹", help="Clean up images and files from posted requests"):
            action_to_clean_images_and_files()
            st.success("Images and files cleaned up successfully.")

        if st.button("Generate Monthly Report", icon="📊", help="Download the monthly report"):
            path, message = get_statistics(year=datetime.now().year, month=datetime.now().month)
            if path:
                st.success(f"Report generated successfully")
                with open(path, "rb") as file:
                    file_contents = file.read()

                # Get just the filename from the full path
                filename = os.path.basename(path)

                # Offer the file for download
                st.download_button(
                    label="Download Report",
                    data=file_contents,
                    file_name=filename,
                    mime="text/html",
                    help="Click to download the HTML report",
                    icon = "📥",
                )

            else:
                st.error(f"Failed: {message}")

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
        with st.expander(f"{row.get('user_name', 'N/A')} ({row.get('user_email','N/A')}) - {row.get('state', 'N/A')} ",
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

            if 'file' in row and row['file']:
                st.subheader(f"Attached Files ({len(row['file'])})")
                cols = st.columns(min(3, len(row['file'])))
                for i, img_url in enumerate(row['file']):
                    with cols[i % 3]:
                        path = REPO_URL + img_url
                        path = path.replace(' ', '%20')

                        st.markdown(f"[Download File {i}]({path})", unsafe_allow_html=True)

            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Posted", key=f"approve_{row_index}"):
                    request_posted(row)
                    st.success("Request marked as posted.")
            with col2:
                if st.button("Generate Email", key=f"email_{row_index}"):
                    email_content = generate_email_content(row)
                    st.subheader("Email Content")
                    st.code(email_content, language="markdown")

                    st.success("Email generated successfully.")








if __name__ == "__main__":
    main()