import datetime
import os

import pytz
from github import Github
import streamlit as st
import json

GITHUB_TOKEN = st.secrets["github_token"]  # Use Streamlit secrets in production
REPO_NAME = "karendcl/fbio-web-requests"  # Your repo
FILE_PATH = "data.json"  # Path to your JSON file
BRANCH = "main"  # Branch to update


def update_json(new_data):
    """Update JSON file on GitHub with new data and upload images"""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    try:
        # Get current JSON file
        file = repo.get_contents(FILE_PATH, ref=BRANCH)
        sha = file.sha
        current_data = json.loads(file.decoded_content.decode())
    except:
        # File doesn't exist yet
        sha = None
        current_data = []

    print("Current data:", current_data)
    print("New data:", new_data)

    # Handle image uploads
    uploaded_image_paths = []
    for img_path in new_data['images']:
        try:
            # Read the image file
            img_name1 = img_path[5:]
            with open(img_path, 'rb') as img_file:
                img_content = img_file.read()

            # Create filename with timestamp to avoid conflicts
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            img_name = f"image_{timestamp}_{img_name1}"
            github_img_path = f"data/{img_name}"

            # Upload to GitHub
            repo.create_file(
                path=github_img_path,
                message=f"Add image {img_name}",
                content=img_content,
                branch=BRANCH
            )
            uploaded_image_paths.append(github_img_path)
        except Exception as e:
            print(f"Failed to upload image {img_path}: {str(e)}")

    # Update the image paths in the new_data before saving
    new_data['images'] = uploaded_image_paths

    # Handle file uploads
    uploaded_file_path = ''
    if new_data['file']:
        try:
            file_path = new_data['file']
            # Read the image file
            img_name1 = file_path[5:]
            with open(file_path, 'rb') as img_file:
                img_content = img_file.read()

            # Create filename with timestamp to avoid conflicts
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            img_name = f"file_{timestamp}_{img_name1}"
            github_img_path = f"data/{img_name}"

            # Upload to GitHub
            repo.create_file(
                path=github_img_path,
                message=f"Add file {img_name}",
                content=img_content,
                branch=BRANCH
            )
            uploaded_file_path = github_img_path
        except Exception as e:
            print(f"Failed to upload file {file_path}: {str(e)}")

    # Update the image paths in the new_data before saving
    new_data['file'] = uploaded_file_path

    # Append the new data (with updated image paths)
    current_data.append(new_data)

    print("Updated data:", current_data)

    # Commit message
    tz = pytz.timezone('UTC')
    timestamp = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
    commit_message = f"Automated update via Streamlit form at {timestamp}"

    # Update the JSON file
    repo.update_file(
        path=FILE_PATH,
        message=commit_message,
        content=json.dumps(current_data, indent=4),
        sha=sha,
        branch=BRANCH
    )
