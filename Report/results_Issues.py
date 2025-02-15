import os
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, dash_table

# Cartella con i file CSV
folder_path = os.path.dirname(os.path.abspath(__file__))  # Modifica con il percorso della tua cartella

# Trova tutti i file che contengono "issues" nel nome
files = [f for f in os.listdir(folder_path) if "issues" in f.lower() and f.endswith(".csv")]

# Legge e combina i file CSV
dfs = [pd.read_csv(os.path.join(folder_path, file)) for file in files]
df = pd.concat(dfs, ignore_index=True)

# Preparazione dati per i grafici
df_tipo = df['Tipo'].value_counts().reset_index()
df_tipo.columns = ['Tipo', 'Conteggio']

df_file = df['File'].value_counts().reset_index()
df_file.columns = ['File', 'Numero di Problemi']

# Avvia l'app Dash
app = dash.Dash(__name__)
app.title = "Analisi Issues Multipli"

# Layout della dashboard
app.layout = html.Div([
    html.H1("Dashboard Analisi Issues", style={'textAlign': 'center'}),
    
    dcc.Graph(id='severity_pie',
              figure=px.pie(df, names='Severità', title='Distribuzione per Severità', hole=0.4)),
    
    dcc.Graph(id='type_bar',
              figure=px.bar(df_tipo, x='Tipo', y='Conteggio',
                             title='Numero di Problemi per Tipo', labels={'Tipo': 'Tipo', 'Conteggio': 'Numero di Problemi'})),
    
    dcc.Graph(id='file_bar',
              figure=px.bar(df_file, x='File', y='Numero di Problemi',
                             title='File con più Problemi', labels={'File': 'File', 'Numero di Problemi': 'Conteggio'})),
    
    html.H2("Tabella Dettagliata dei Problemi"),
    dash_table.DataTable(
        id='table',
        columns=[{'name': col, 'id': col} for col in df.columns],
        data=df.to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto'}
    )
])

# Avvio del server Dash
if __name__ == '__main__':
    app.run_server(debug=True)
