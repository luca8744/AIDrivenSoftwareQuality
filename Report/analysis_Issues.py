import pandas as pd
import plotly.graph_objects as go
import os
from plotly.subplots import make_subplots

def analyze_issue_reports(directory):
    files = [f for f in os.listdir(directory) if "issue" in f.lower() and f.endswith(".csv")]

    if not files:
        print("Nessun file trovato.")
        return

    num_files = len(files)
    fig = make_subplots(
        rows=num_files, cols=3, 
        subplot_titles=["Numero Totale di Issue", "Distribuzione per Severità", "Distribuzione per Tipologia"],
        specs=[[{"type": "indicator"}, {"type": "pie"}, {"type": "pie"}] for _ in files],
        vertical_spacing=0.05  # Reduce spacing for a better layout
    )

    for i, file in enumerate(files, start=1):
        file_path = os.path.join(directory, file)
        df = pd.read_csv(file_path, encoding='utf-8', header=None)
        total_issues = df.shape[0]

        # Severity Counts
        severity_counts = df[3].value_counts().reset_index()
        severity_counts.columns = ["Severità", "Count"]
        severity_counts = severity_counts[severity_counts["Count"] / total_issues > 0.01]

        # Type Counts
        type_counts = df[2].value_counts().reset_index()
        type_counts.columns = ["Tipologia", "Count"]
        type_counts = type_counts[type_counts["Count"] / total_issues > 0.01]

        # 🔹 Indicator - Reduced Font Size
        fig.add_trace(go.Indicator(
            mode="number",
            value=total_issues,
            title={"text": f"{file}", 'font': {'size': 12}}  # Reduced font size
        ), row=i, col=1)

        # 🔹 Pie Chart for Severity - Set Scale
        if not severity_counts.empty:
            fig.add_trace(go.Pie(
                labels=severity_counts["Severità"], 
                values=severity_counts["Count"], 
                hole=0.3, 
                scalegroup=f"group_{i}"  # Keeps pie charts uniform
            ), row=i, col=2)

        # 🔹 Pie Chart for Type - Set Scale
        if not type_counts.empty:
            fig.add_trace(go.Pie(
                labels=type_counts["Tipologia"], 
                values=type_counts["Count"], 
                hole=0.3, 
                scalegroup=f"group_{i}"  # Keeps pie charts uniform
            ), row=i, col=3)

    # 🔹 Adjust Layout to Increase Pie Chart Size
    fig.update_layout(
        title_text="Analisi delle Issue per File", 
        showlegend=True, 
        width=1400,   # Increased width
        height=600 * num_files  # More height to avoid crowding
    )
    
    fig.show()

analyze_issue_reports(os.path.dirname(os.path.abspath(__file__)))
