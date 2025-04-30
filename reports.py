import json

import markdown
import streamlit as st
from github import Github
import pandas as pd
from matplotlib import pyplot as plt
from weasyprint import HTML

REPO_URL = "https://raw.githubusercontent.com/karendcl/fbio-web-requests/main/"
GITHUB_TOKEN = st.secrets["github_token"]  # Use Streamlit secrets in production
REPO_NAME = "karendcl/fbio-web-requests"  # Your repo
FILE_PATH = "data.json"  # Path to your JSON file
BRANCH = "main"  # Branch to update


def get_json():
    """Get the JSON file from GitHub."""
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

    return current_data


import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

def generate_graphs(dept_stats, timestamp, report_dir):
    # Generate charts
    plt.figure(figsize=(10, 6))
    dept_stats['Total de Solicitudes'].plot.pie(autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Total de Solicitudes por Departamento')
    pie_chart_name = f'total_requests_pie_{timestamp}.png'
    pie_chart_path = os.path.join(report_dir, pie_chart_name)
    plt.savefig(pie_chart_path)
    plt.close()

    plt.figure(figsize=(12, 6))
    dept_stats[['Pendiente', 'Publicada']].plot(kind='bar')
    plt.title('Estado de Solicitudes por Departamento')
    plt.xlabel('Departmento')
    plt.ylabel('Cantidad de Solicitudes')
    # labels horizontally
    plt.xticks(rotation=45)
    plt.legend(title='Estado de Solicitud', labels=['Pendiente', 'Publicada'])
    plt.tight_layout()

    bar_chart_name = f'requests_status_bar_{timestamp}.png'
    bar_chart_path = os.path.join(report_dir, bar_chart_name)
    plt.savefig(bar_chart_path)
    plt.close()

    return pie_chart_path, bar_chart_path

def generate_report_html(month, year, total_requests, total_pending, total_approved, dept_stats, pie_chart_path, bar_chart_path,
                         report_dir, timestamp, user_stats, total_approved_perc, total_historical_approved_perc,
                         total_historical_requests, total_historical_pending, total_historical_approved):
    heading = f"Reporte {'mensual' if month else 'anual'} {'- ' + str(month) if month else ''} {year if year else ''}"
    date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # Generate report by taking the report_template in html and replacing the variables
    template_url = 'report_template.html'
    with open(template_url, 'r', encoding='utf-8') as f:
        report_template = f.read()

    report_template = report_template.replace("DATE", date)
    report_template = report_template.replace("TOTAL_HISTORICAL_REQUESTS", str(total_historical_requests))
    report_template = report_template.replace("TOTAL_HISTORICAL_PENDING", str(total_historical_pending))
    report_template = report_template.replace("TOTAL_HISTORICAL_APPROVED_PERC", str(total_historical_approved_perc))
    report_template = report_template.replace("TOTAL_HISTORICAL_APPROVED", str(total_historical_approved))


    report_template = report_template.replace("HEADING", heading)
    report_template = report_template.replace("TOTAL_REQUESTS", str(total_requests))
    report_template = report_template.replace("TOTAL_PENDING", str(total_pending))
    report_template = report_template.replace("TOTAL_APPROVED_PERC", str(total_approved_perc))
    report_template = report_template.replace("TOTAL_APPROVED", str(total_approved))
    report_template = report_template.replace("DEPARTMENT_TABLES", dept_stats.to_html())
    report_template = report_template.replace("USER_TABLES", user_stats.to_html())
    report_template = report_template.replace("IMAGE_TOTAL_DEPARTMENTS", pie_chart_path)
    report_template = report_template.replace("IMAGE_STATE_DEPARTMENTS", bar_chart_path)
    # Save report
    report = markdown.markdown(report_template)
    report_path = os.path.join(report_dir, f'report_{timestamp}.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    return report_path

def get_statistics(year=None, month=None):
    try:
        # Load and prepare data
        df = pd.DataFrame(get_json())
        df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y%m%d_%H%M%S")

        total_historical_requests = len(df)
        total_historical_pending = len(df[df['state'] == 'pending'])
        total_historical_approved = len(df[df['state'] == 'posted'])
        total_historical_approved_perc = round(((total_historical_approved / total_historical_requests) * 100), 2) if total_historical_requests > 0 else 0

        # Filter data
        if year:
            df = df[df['timestamp'].dt.year == year]
        if month:
            df = df[df['timestamp'].dt.month == month]

        # Calculate statistics
        total_requests = len(df)
        total_pending = len(df[df['state'] == 'pending'])
        total_approved = len(df[df['state'] == 'posted'])
        total_approved_perc = round(((total_approved / total_requests) * 100), 2) if total_requests > 0 else 0

        # Department-wise statistics
        # Department statistics - FIXED THE COLUMN MISMATCH HERE
        dept_counts = df['department'].value_counts().reset_index()
        dept_counts.columns = ['Departmento', 'Total de Solicitudes']  # Only 2 columns here

        # Calculate pending and approved separately
        pending = df[df['state'] == 'pending']['department'].value_counts()
        approved = df[df['state'] == 'posted']['department'].value_counts()

        # Merge all statistics
        dept_stats = dept_counts.merge(
            pending.rename('Pendiente'),
            left_on='Departmento',
            right_index=True,
            how='left'
        ).merge(
            approved.rename('Publicada'),
            left_on='Departmento',
            right_index=True,
            how='left'
        ).fillna(0)

        # Convert counts to integers
        dept_stats['Pendiente'] = dept_stats['Pendiente'].astype(int)
        dept_stats['Publicada'] = dept_stats['Publicada'].astype(int)

        # Final formatting
        dept_stats['Departmento'] = dept_stats['Departmento'].str.capitalize()
        dept_stats = dept_stats.sort_values('Total de Solicitudes', ascending=False)


        # Add a column for the percentage of posted requests per department
        dept_stats['% Publicada'] = (dept_stats['Publicada'] / dept_stats['Total de Solicitudes']) * 100
        dept_stats['% Publicada'] = dept_stats['% Publicada'].fillna(0).round(2)
        dept_stats['% Publicada'] = dept_stats['% Publicada'].astype(str) + '%'


        # Add a column for the percentage of posted requests per department
        dept_stats['% Publicada del total'] = (dept_stats['Publicada'] / total_approved) * 100
        dept_stats['% Publicada del total'] = dept_stats['% Publicada del total'].fillna(0).round(2)
        dept_stats['% Publicada del total'] = dept_stats['% Publicada del total'].astype(str) + '%'

        user_stats = (
            df.groupby('user_email')
            .agg(
                Total_Solicitudes=('user_email', 'count'),
                Departamento=('department', lambda x: x.mode()[0] if len(x.mode()) > 0 else 'N/A')
            )
            .reset_index()
            .rename(columns={
                'user_email': 'Usuario',
                'Total_Solicitudes': 'Total Solicitudes',
                'Departamento': 'Departamento'
            })
        )

        # Calculate percentage of total requests
        user_stats['% del Total'] = (
                (user_stats['Total Solicitudes'] / total_requests * 100)
                .round(2)
                .astype(str) + '%'
        )

        # Sort by most active users
        user_stats = user_stats.sort_values('Total Solicitudes', ascending=False)

        # Reset index for cleaner output
        user_stats = user_stats.reset_index(drop=True)

        # Create output directory if it doesn't exist
        report_dir = os.path.join(os.getcwd(), 'reports')
        os.makedirs(report_dir, exist_ok=True)

        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        pie_chart_path, bar_chart_path = generate_graphs(dept_stats, timestamp, report_dir)

        report_path = generate_report_html(month, year, total_requests, total_pending, total_approved,
                                           dept_stats, pie_chart_path, bar_chart_path,
                                           report_dir, timestamp, user_stats, total_approved_perc, total_historical_approved_perc,
                                           total_historical_requests, total_historical_pending, total_historical_approved)
        return report_path, 'success'

    except Exception as e:
        return None, str(e)


















